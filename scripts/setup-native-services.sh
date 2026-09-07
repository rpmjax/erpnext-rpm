#!/usr/bin/env bash
# Reproduce the native service setup on the inspected Ubuntu VM.
set -euo pipefail
umask 022

BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
BENCH_USER="$(id -un)"
if [[ "$EUID" -eq 0 ]]; then
    echo 'Run as the bench owner, not root; sudo is used only where required.' >&2
    exit 1
fi
cd "$BENCH_DIR"
[[ -f sites/common_site_config.json && -x env/bin/gunicorn ]]
command -v bench >/dev/null
sudo -v

# Preserve configuration containing credentials outside the repository.
BACKUP_DIR="$HOME/rpm-ops-backups/$(date +%Y%m%d-%H%M%S)"
install -d -m 700 "$BACKUP_DIR"
install -m 600 sites/common_site_config.json "$BACKUP_DIR/common_site_config.json"
for config in config/nginx.conf config/supervisor.conf; do
    if [[ -f "$config" ]]; then
        install -m 600 "$config" "$BACKUP_DIR/$(basename "$config")"
    fi
done

sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y nginx supervisor acl
bench set-config -gp gunicorn_workers 3
bench setup supervisor --user "$BENCH_USER" --yes
bench setup nginx --yes --log_format combined
sudo setfacl -m u:www-data:--x "$HOME"

link_config() {
    local source="$1" target="$2"
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ "$(readlink -f "$target")" != "$source" ]]; then
            echo "Existing unrelated configuration: $target. Resolve it before retrying." >&2
            exit 1
        fi
    else
        sudo ln -s "$source" "$target"
    fi
}
link_config "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf
link_config "$BENCH_DIR/config/nginx.conf" /etc/nginx/conf.d/frappe-bench.conf

# Only disable the package's standard symlink; retain the default file itself.
if [[ -L /etc/nginx/sites-enabled/default ]]; then
    [[ "$(readlink -f /etc/nginx/sites-enabled/default)" == /etc/nginx/sites-available/default ]]
    [[ ! -e /etc/nginx/sites-available/default.disabled-link && ! -L /etc/nginx/sites-available/default.disabled-link ]]
    sudo mv /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default.disabled-link
fi
sudo nginx -t
sudo systemctl enable --now nginx supervisor mariadb
sudo supervisorctl reread
sudo supervisorctl update
sudo systemctl reload nginx
sudo supervisorctl status
bench doctor
