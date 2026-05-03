# browser-deploy

LXC + nginx + systemd artifacts for deploying BitCoinTrader behind HAProxy on
the moorelab homelab.

## Topology

```
Browser (https://bitcointrader.moorelab.cloud/)
   │  TLS terminates at HAProxy
   ▼
HAProxy on opnsense-primary (10.1.0.240)
   │  ACL: hdr(host) == bitcointrader.moorelab.cloud
   │  → backend: bitcointrader-backend → 10.1.40.103:80
   ▼
nginx on LXC bitcointrader (10.1.40.103, CT 202 on proxmox2)
   │  reverse-proxies / and /ws → 127.0.0.1:8080
   ▼
uvicorn  (bitcointrader.server.app, port 8080)
   │  FastAPI: serves website/index.html + /ws WebSocket
   ▼
MarketEngine (one process, all sessions share the same market)
```

## Files

- `nginx/bitcointrader.conf` — single server block, proxies everything to 127.0.0.1:8080
- `systemd/bitcointrader.service` — runs `python -m bitcointrader.main --port 8080`
- `scripts/provision_lxc.sh` — one-shot provisioning of a fresh Debian 12 LXC
- `scripts/deploy.sh` — pull-and-restart script for code updates

## Deploy flow

1. `bash scripts/provision_lxc.sh` — runs once on the new LXC
2. `bash scripts/deploy.sh` — runs every time `main` updates
