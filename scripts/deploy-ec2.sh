#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${REPO_URL:-https://github.com/ellis-li-lhc/exam-study-hub.git}"
RELEASE_REF="${RELEASE_REF:-c6cb143d4d71749532a202d8de1d1935d22f42d7}"
APP_DIR="${APP_DIR:-/opt/exam-study-hub}"
WEB_DIR="${WEB_DIR:-/var/www/exam-study-hub}"
BACKUP_BASE="${BACKUP_BASE:-/var/backups/exam-study-hub}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run with sudo: sudo bash scripts/deploy-ec2.sh" >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
work_dir="$(mktemp -d /var/tmp/exam-study-hub-deploy.XXXXXX)"
backup_dir="${BACKUP_BASE}/${timestamp}-${RELEASE_REF}"
service_stopped=0

cleanup() {
  rm -rf "${work_dir}"
}
trap cleanup EXIT

handle_error() {
  exit_code=$?
  trap - ERR
  set +e
  if [[ "${service_stopped}" -eq 1 ]]; then
    systemctl start exam-study-hub
  fi
  echo "Deployment failed. Current service was restarted; backup: ${backup_dir}" >&2
  exit "${exit_code}"
}
trap handle_error ERR

echo "[1/8] Preparing build tools"
if ! command -v git >/dev/null || ! command -v npm >/dev/null; then
  dnf install -y git nodejs npm
fi

echo "[2/8] Fetching release ${RELEASE_REF}"
git clone --quiet --no-checkout "${REPO_URL}" "${work_dir}/repo"
git -C "${work_dir}/repo" fetch --quiet --depth 1 origin "${RELEASE_REF}"
git -C "${work_dir}/repo" checkout --quiet --detach FETCH_HEAD
actual_ref="$(git -C "${work_dir}/repo" rev-parse --short HEAD)"
if [[ "${actual_ref}" != "${RELEASE_REF:0:${#actual_ref}}" && "${RELEASE_REF}" != "main" ]]; then
  echo "Release mismatch: expected ${RELEASE_REF}, got ${actual_ref}" >&2
  exit 1
fi

echo "[3/8] Building frontend"
pushd "${work_dir}/repo/exam-study-hub-client" >/dev/null
npm ci --no-audit --no-fund
npm run build
popd >/dev/null

echo "[4/8] Backing up database and current release"
mkdir -p "${backup_dir}"
sudo -u postgres pg_dump -Fc exam_study > "${backup_dir}/exam_study.dump"
tar -czf "${backup_dir}/server.tar.gz" -C "${APP_DIR}/server" .
tar -czf "${backup_dir}/client-dist.tar.gz" -C "${WEB_DIR}" .

echo "[5/8] Installing backend dependencies"
"${APP_DIR}/venv/bin/pip" install \
  --disable-pip-version-check \
  --no-cache-dir \
  -r "${work_dir}/repo/exam-study-hub-server/requirements.txt"

echo "[6/8] Publishing server and frontend files"
systemctl stop exam-study-hub
service_stopped=1
find "${APP_DIR}/server" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
tar -C "${work_dir}/repo/exam-study-hub-server" -cf - . \
  | tar -C "${APP_DIR}/server" -xf -
find "${WEB_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
tar -C "${work_dir}/repo/exam-study-hub-client/dist" -cf - . \
  | tar -C "${WEB_DIR}" -xf -

chown -R root:examstudy "${APP_DIR}/server"
chmod -R g=rX,o= "${APP_DIR}/server"
chown -R root:root "${WEB_DIR}"
find "${WEB_DIR}" -type d -exec chmod 0755 {} +
find "${WEB_DIR}" -type f -exec chmod 0644 {} +

echo "[7/8] Applying migrations and Zhejiang seed data"
database_url="$(sed -n 's/^DATABASE_URL=//p' /etc/exam-study-hub/database.env)"
if [[ -z "${database_url}" ]]; then
  echo "DATABASE_URL is missing from /etc/exam-study-hub/database.env" >&2
  exit 1
fi
pushd "${APP_DIR}/server" >/dev/null
sudo -u examstudy env DATABASE_URL="${database_url}" \
  "${APP_DIR}/venv/bin/alembic" upgrade head
sudo -u examstudy env DATABASE_URL="${database_url}" \
  "${APP_DIR}/venv/bin/python" -m scripts.seed
popd >/dev/null

echo "[8/8] Restarting and verifying services"
nginx -t
systemctl restart exam-study-hub
service_stopped=0
systemctl reload nginx

for attempt in {1..30}; do
  if curl -fsS http://127.0.0.1:8080/api/health >/dev/null; then
    break
  fi
  if [[ "${attempt}" -eq 30 ]]; then
    echo "Health check failed. Backup: ${backup_dir}" >&2
    systemctl status exam-study-hub --no-pager || true
    exit 1
  fi
  sleep 1
done

zhejiang_counts="$(sudo -u postgres psql -d exam_study -At -F, -c \
  "SELECT
     (SELECT count(*) FROM institutions i JOIN provinces p ON p.id=i.province_id WHERE p.code='zhejiang'),
     (SELECT count(*) FROM admission_plans ap JOIN institutions i ON i.id=ap.institution_id JOIN provinces p ON p.id=i.province_id WHERE p.code='zhejiang'),
     (SELECT count(*) FROM province_control_scores pcs JOIN provinces p ON p.id=pcs.province_id WHERE p.code='zhejiang');")"

echo "Deployment complete"
echo "Release: ${actual_ref}"
echo "Backup: ${backup_dir}"
echo "Zhejiang counts (institutions,plans,control_scores): ${zhejiang_counts}"
