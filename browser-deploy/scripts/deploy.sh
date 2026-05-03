#!/usr/bin/env bash
# Pull latest code and restart. Run as root on the LXC.
set -euo pipefail

DEPLOY_DIR="/opt/bitcointrader/repo"
SVC_USER="bitcointrader"

cd "${DEPLOY_DIR}"
sudo -u "${SVC_USER}" git pull origin main
sudo -u "${SVC_USER}" .venv/bin/pip install -e . -q

systemctl restart bitcointrader

echo "Deployed. Service restarting…"
systemctl status bitcointrader --no-pager
