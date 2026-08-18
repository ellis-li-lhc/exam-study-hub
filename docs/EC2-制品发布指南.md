# EC2 制品发布

适用于 `study.hongchangli.xyz`。前端在本机构建，VPS 不安装或运行 Node 构建。

## 本机构建与打包

```bash
cd /Users/lihongchang/MyCodeProject/exam-study-hub/exam-study-hub-client
npm run build

release_dir=$(mktemp -d /tmp/exam-study-release.XXXXXX)
cd /Users/lihongchang/MyCodeProject/exam-study-hub
COPYFILE_DISABLE=1 tar -czf "$release_dir/server.tar.gz" --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='.pytest_cache' --exclude='._*' --exclude='.DS_Store' -C exam-study-hub-server .
COPYFILE_DISABLE=1 tar -czf "$release_dir/client-dist.tar.gz" --exclude='._*' --exclude='.DS_Store' -C exam-study-hub-client/dist .
```

`._*` 和 `.DS_Store` 必须排除，否则 macOS 隐藏文件可能让 Alembic 迁移失败。

## 上传和发布

临时只允许本机 SSH 后，上传两个制品和发布脚本：

```bash
scp -i ~/Downloads/tokyo-vpn-key.pem "$release_dir/server.tar.gz" "$release_dir/client-dist.tar.gz" ec2-user@<EC2_IP>:/tmp/
scp -i ~/Downloads/tokyo-vpn-key.pem scripts/deploy-artifact-release.sh ec2-user@<EC2_IP>:/tmp/
ssh -i ~/Downloads/tokyo-vpn-key.pem ec2-user@<EC2_IP> 'sudo bash /tmp/deploy-artifact-release.sh /tmp'
```

脚本会备份数据库、后端和前端静态文件，然后迁移数据库、写入公开数据、重启服务并检查健康接口。

## 验证与收尾

```bash
curl -fsS https://study.hongchangli.xyz/api/health
```

验证成功后，立刻删除安全组中为上传临时添加的 SSH 入站规则；保留 EC2 Instance Connect 的 `3.112.23.0/29` 规则即可。
