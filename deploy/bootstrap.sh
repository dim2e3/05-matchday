#!/usr/bin/env bash
# One-time EC2 host setup (Amazon Linux 2023 or Ubuntu). Run as the SSH user with sudo:
#   scp -r deploy ec2-user@<ip>:/tmp/ && ssh ec2-user@<ip> 'bash /tmp/deploy/bootstrap.sh'
# Idempotent: safe to re-run.
set -euo pipefail

if ! command -v docker >/dev/null; then
  if command -v dnf >/dev/null; then
    sudo dnf install -y docker
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    arch=$(uname -m)
    sudo curl -fsSL -o /usr/local/lib/docker/cli-plugins/docker-compose \
      "https://github.com/docker/compose/releases/download/v2.40.3/docker-compose-linux-${arch}"
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  else
    curl -fsSL https://get.docker.com | sudo sh
  fi
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$USER"
  echo "Docker installed; log out and back in (or 'newgrp docker') before deploying."
fi

# 2 GB swap: two app stacks + the telemetry stack on a small instance.
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

sudo mkdir -p /opt/matchday/{dev,prod,edge,ops}
sudo chown -R "$USER" /opt/matchday

sudo docker network inspect edge >/dev/null 2>&1 || sudo docker network create edge
sudo docker network inspect ops >/dev/null 2>&1 || sudo docker network create ops

echo "Bootstrap done. Open ports 80 and 443 in the instance's security group."
