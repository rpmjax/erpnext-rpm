#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
repo_dir=$PWD
state_dir=${RPM_STATE_DIR:-"$HOME/.config/rpm-worklog-vm"}
if [[ "$state_dir" != /* || "$state_dir" == *' '* ]]; then echo 'RPM_STATE_DIR must be an absolute path without spaces'; exit 1; fi
config_file="$state_dir/deploy.env"
command=${1:-help}
if [[ "$command" == configure ]]; then
    umask 077
    mkdir -p "$state_dir"
    if [[ -e "$config_file" ]]; then echo "Configuration exists: $config_file (not overwritten)"; exit 1; fi
    command -v openssl >/dev/null
    printf 'RPM_PROJECT=rpm-worklog-vm\nRPM_SITE=worklog.internal\nRPM_BIND_IP=127.0.0.1\nRPM_PORT=8085\nRPM_STATE_DIR=%s\nRPM_IMAGE=rpm-worklog-vm:unbuilt\n' "$state_dir" > "$config_file"
    openssl rand -hex 24 > "$state_dir/db-password"
    openssl rand -hex 24 > "$state_dir/admin-password"
    # Parent directory 700 protects secrets; files must be readable by the frappe container UID.
    chmod 700 "$state_dir"
    chmod 644 "$state_dir/db-password" "$state_dir/admin-password"
    echo "Created $config_file. Review site/port before init. Administrator password: $state_dir/admin-password"
    exit 0
fi
if [[ ! -f "$config_file" ]]; then echo 'Run: bash deploy/deploy.sh configure'; exit 1; fi
# This is a private, administrator-owned configuration file.
set -a
source "$config_file"
set +a
compose() { docker compose --env-file "$config_file" -p "$RPM_PROJECT" -f "$repo_dir/deploy/compose.yaml" "$@"; }

service_snapshot() {
    local service=$1 cid state
    cid=$(compose ps -a -q "$service")
    [[ -n "$cid" && "$cid" != *$'\n'* ]] || return 1
    state=$(docker inspect --format '{{.State.Running}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid")
    [[ "$state" == 'true healthy' || "$state" == 'true none' ]] || return 1
    docker inspect --format '{{.Id}} {{.RestartCount}} {{.State.StartedAt}}' "$cid"
}
verify_services() {
    local service attempt ready current tick
    local services=(db redis-cache redis-queue backend websocket queue-short queue-long scheduler frontend)
    local -A baseline
    for attempt in {1..12}; do
        ready=1
        for service in "${services[@]}"; do
            if ! baseline[$service]=$(service_snapshot "$service"); then ready=0; fi
        done
        if [[ "$ready" == 1 ]]; then break; fi
        echo 'Waiting for all services to run and health checks to pass...'
        sleep 5
    done
    if [[ "$ready" != 1 ]]; then compose ps -a; echo 'Service readiness failed; run logs.'; return 1; fi
    echo 'Checking all 9 services for 60 seconds without restarts...'
    for tick in {1..12}; do
        sleep 5
        for service in "${services[@]}"; do
            current=$(service_snapshot "$service") || { echo "Unstable service: $service"; return 1; }
            [[ "$current" == "${baseline[$service]}" ]] || { echo "Service restarted: $service"; return 1; }
        done
    done
    echo 'SERVICES_STABLE: all 9 running; health checks pass; no restarts during observation.'
}
case "$command" in
    build)
        if [[ -n "$(git status --porcelain)" && "${RPM_ALLOW_DIRTY:-0}" != 1 ]]; then echo 'Commit tracked changes before building a release'; exit 1; fi
        image="rpm-worklog-vm:$(git rev-parse --short=12 HEAD)"
        docker build -f docker/Dockerfile.worklog -t "$image" .
        sed -i "s|^RPM_IMAGE=.*|RPM_IMAGE=$image|" "$config_file"
        echo "Built $image"
        ;;
    init)
        compose --profile setup run --rm init
        compose up -d db redis-cache redis-queue backend websocket queue-short queue-long scheduler frontend
        verify_services
        ;;
    status)
        compose ps -a
        compose exec -T backend bench --site "$RPM_SITE" list-apps
        ;;
    backup)
        compose exec -T backend bench --site "$RPM_SITE" backup --with-files
        stamp=$(date -u +%Y%m%dT%H%M%SZ)
        target="$state_dir/backups/$stamp"
        mkdir -p "$target"
        chmod 700 "$state_dir/backups" "$target"
        compose cp "backend:/home/frappe/frappe-bench/sites/$RPM_SITE/private/backups/." "$target/"
        compose cp "backend:/home/frappe/frappe-bench/sites/$RPM_SITE/site_config.json" "$target/site_config.json"
        cp "$config_file" "$target/deploy.env"
        docker inspect --format '{{.Config.Image}} {{.Image}}' "$(compose ps -q backend)" > "$target/running-image.txt"
        chmod -R go-rwx "$target"
        echo "Backup copied to $target; copy this outside the VM and test restoration."
        ;;
    update)
        # New image must already be built; backup command still runs in the old container.
        compose exec -T backend bench --site "$RPM_SITE" set-maintenance-mode on
        compose stop -t 120 scheduler queue-short queue-long frontend websocket
        bash deploy/deploy.sh backup
        compose stop backend
        # On failure keep services stopped/maintenance enabled for operator recovery.
        compose run --rm --no-deps backend bench --site "$RPM_SITE" migrate
        compose up -d backend websocket queue-short queue-long scheduler frontend
        compose exec -T backend bench --site "$RPM_SITE" set-maintenance-mode off
        verify_services
        ;;
    verify) verify_services ;;
    repair-workers)
        compose up -d --no-deps queue-short queue-long
        verify_services
        ;;
    enroll)
        [[ $# == 3 ]] || { echo 'Usage: enroll USER_EMAIL employee|manager'; exit 1; }
        [[ "$3" == employee || "$3" == manager ]] || exit 1
        # JSON encoding happens inside Python, never interpolated into executable code.
        compose exec -T backend /home/frappe/frappe-bench/env/bin/python -c 'import json,subprocess,sys; subprocess.run(["bench","--site",sys.argv[1],"execute","rpm_worklog.bootstrap.enroll","--kwargs",json.dumps({"user":sys.argv[2],"manager":sys.argv[3]=="manager"})],check=True)' "$RPM_SITE" "$2" "$3"
        ;;
    logs) compose logs --tail 100 backend frontend queue-short queue-long scheduler ;;
    *) echo 'Commands: configure | build | init | status | verify | repair-workers | backup | update | enroll EMAIL employee|manager | logs' ;;
esac
