#!/usr/bin/env bash
# Provision a fresh Debian 12 LXC for BitCoinTrader.
# Run as root inside the container.
#
# SSH keys are NOT hardcoded here.  Before running, copy your authorized_keys
# to the container or set SSH_AUTHORIZED_KEYS_FILE:
#
#   scp ~/.ssh/authorized_keys root@bitcointrader:/tmp/authorized_keys
#   SSH_AUTHORIZED_KEYS_FILE=/tmp/authorized_keys bash provision_lxc.sh
#
# Or fetch from GitHub (recommended — no paste hassle):
#   SSH_AUTHORIZED_KEYS="$(curl -sS https://github.com/tricheboars.keys)" \
#     bash provision_lxc.sh
set -euo pipefail

REPO_URL="https://github.com/tricheboars/BitCoinTrader.git"
DEPLOY_DIR="/opt/bitcointrader/repo"
SVC_USER="bitcointrader"

# ── System packages ───────────────────────────────────────────────────────────
apt update && apt upgrade -y
apt install -y \
  git python3 python3-venv python3-pip \
  nginx curl wget htop sudo \
  build-essential libssl-dev

# ── SSH key auth ──────────────────────────────────────────────────────────────
mkdir -p /root/.ssh
chmod 700 /root/.ssh

if [[ -n "${SSH_AUTHORIZED_KEYS_FILE:-}" && -f "${SSH_AUTHORIZED_KEYS_FILE}" ]]; then
  cat "${SSH_AUTHORIZED_KEYS_FILE}" >> /root/.ssh/authorized_keys
elif [[ -n "${SSH_AUTHORIZED_KEYS:-}" ]]; then
  echo "${SSH_AUTHORIZED_KEYS}" >> /root/.ssh/authorized_keys
else
  echo "WARNING: no SSH keys provided — set SSH_AUTHORIZED_KEYS_FILE or SSH_AUTHORIZED_KEYS"
  echo "         You will only be able to log in with the password set via Terraform."
fi

chmod 600 /root/.ssh/authorized_keys 2>/dev/null || true
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# ── Deployment user + directory ───────────────────────────────────────────────
mkdir -p /opt/bitcointrader
useradd -r -s /usr/sbin/nologin -d /opt/bitcointrader "${SVC_USER}" || true
chown "${SVC_USER}:${SVC_USER}" /opt/bitcointrader

# ── Clone repo ────────────────────────────────────────────────────────────────
if [ -d "${DEPLOY_DIR}/.git" ]; then
  echo "Repo already cloned — pulling latest…"
  sudo -u "${SVC_USER}" git -C "${DEPLOY_DIR}" pull origin main
else
  sudo -u "${SVC_USER}" git clone "${REPO_URL}" "${DEPLOY_DIR}"
fi

# ── Python venv + dependencies ────────────────────────────────────────────────
cd "${DEPLOY_DIR}"
sudo -u "${SVC_USER}" python3 -m venv .venv
sudo -u "${SVC_USER}" .venv/bin/pip install --upgrade pip -q
sudo -u "${SVC_USER}" .venv/bin/pip install -e . -q

# ── nginx ─────────────────────────────────────────────────────────────────────
cp "${DEPLOY_DIR}/browser-deploy/nginx/bitcointrader.conf" \
   /etc/nginx/sites-available/bitcointrader
ln -sf /etc/nginx/sites-available/bitcointrader \
       /etc/nginx/sites-enabled/bitcointrader
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl enable nginx && systemctl restart nginx

# ── systemd service ───────────────────────────────────────────────────────────
cp "${DEPLOY_DIR}/browser-deploy/systemd/bitcointrader.service" \
   /etc/systemd/system/bitcointrader.service
systemctl daemon-reload
systemctl enable --now bitcointrader

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "  BitCoinTrader provisioned."
echo ""
echo "  Service     : systemctl status bitcointrader"
echo "  nginx       : systemctl status nginx"
echo "  Local URL   : http://$(hostname -I | awk '{print $1}')/"
echo "  Healthcheck : curl -s http://localhost/healthz"
echo "─────────────────────────────────────────────────────────────────"
