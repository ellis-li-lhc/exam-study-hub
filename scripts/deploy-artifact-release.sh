#!/usr/bin/env bash
set -Eeuo pipefail

artifact_dir="${1:-/tmp}"
app_dir="/opt/exam-study-hub"
web_dir="/var/www/exam-study-hub"
backup_dir="/var/backups/exam-study-hub/$(date -u +%Y%m%dT%H%M%SZ)-artifact"
service_stopped=0

[[ $EUID -eq 0 ]] || { echo "Run as root" >&2; exit 1; }
[[ -f "$artifact_dir/server.tar.gz" && -f "$artifact_dir/client-dist.tar.gz" ]] || { echo "Missing release artifacts" >&2; exit 1; }

restart_on_error() {
  exit_code=$?
  if [[ "$service_stopped" -eq 1 ]]; then
    systemctl start exam-study-hub || true
  fi
  exit "$exit_code"
}
trap restart_on_error ERR

mkdir -p "$backup_dir"
sudo -u postgres pg_dump -Fc exam_study > "$backup_dir/exam_study.dump"
tar -czf "$backup_dir/server.tar.gz" -C "$app_dir/server" .
tar -czf "$backup_dir/client-dist.tar.gz" -C "$web_dir" .

"$app_dir/venv/bin/pip" install --disable-pip-version-check --no-cache-dir -r <(tar -xOf "$artifact_dir/server.tar.gz" ./requirements.txt)

systemctl stop exam-study-hub
service_stopped=1
find "$app_dir/server" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
tar -xzf "$artifact_dir/server.tar.gz" -C "$app_dir/server"
find "$web_dir" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
tar -xzf "$artifact_dir/client-dist.tar.gz" -C "$web_dir"
chown -R root:examstudy "$app_dir/server"
chmod -R g=rX,o= "$app_dir/server"
chown -R root:root "$web_dir"
find "$web_dir" -type d -exec chmod 0755 {} +
find "$web_dir" -type f -exec chmod 0644 {} +

database_url="$(sed -n 's/^DATABASE_URL=//p' /etc/exam-study-hub/database.env)"
cd "$app_dir/server"
sudo -u examstudy env DATABASE_URL="$database_url" "$app_dir/venv/bin/alembic" upgrade head
sudo -u examstudy env DATABASE_URL="$database_url" "$app_dir/venv/bin/python" -m scripts.seed

nginx -t
systemctl restart exam-study-hub
service_stopped=0
systemctl reload nginx
curl -fsS http://127.0.0.1:8080/api/health >/dev/null
echo "Deployment complete; backup: $backup_dir"
