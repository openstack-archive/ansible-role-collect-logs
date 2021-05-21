#!/usr/bin/env bash
set -x

get_engine() {
    if ! command -v docker &>/dev/null ; then echo "podman"; exit; fi
    if ! command -v podman &>/dev/null ; then echo "docker"; exit; fi
    if ! systemctl is-active docker &>/dev/null ; then echo "podman"; exit; fi
    if [[ -z $(docker ps --all -q) ]]; then
        echo "podman";
        exit;
    fi
    if [[ -z $(podman ps --all -q) ]]; then
        echo "docker"; exit;
    fi
    echo 'podman'
}

container_cp() {
    ${engine} cp "${1}:${2}" "$3"
};

engine=$(get_engine)
echo "${engine} was detected."
BASE_CONTAINER_EXTRA=/var/log/extra/${engine};
mkdir -p "$BASE_CONTAINER_EXTRA";
ALL_FILE=$BASE_CONTAINER_EXTRA/${engine}_allinfo.log;

CONTAINER_INFO_CMDS=(
    "${engine} ps --all"
    "${engine} images"
    "${engine} version"
    "${engine} info"
    "${engine} volume ls"
    "${engine} network ls"
);

for cmd in "${CONTAINER_INFO_CMDS[@]}"; do
    {
    echo "+ $cmd"
    $cmd
    echo ""
    echo ""
    } >> "$ALL_FILE"
done;

# Get only failed containers, in a dedicated file
${engine} ps -a | grep -vE ' (IMAGE|Exited \(0\)|Up) ' &>> /var/log/extra/failed_containers.log;

# Get inspect infos for all containers even the ones not running.
for cont in $(${engine} ps -a | awk '{print $NF}' | grep -v NAMES); do
    INFO_DIR=$BASE_CONTAINER_EXTRA/containers/${cont};
    mkdir -p "$INFO_DIR";
    (
        ${engine} inspect "$cont";
    ) &> "$INFO_DIR/${engine}_info.log";
done;

# Get other infos for running containers
for cont in $(${engine} ps | awk '{print $NF}' | grep -v NAMES); do
    INFO_DIR=$BASE_CONTAINER_EXTRA/containers/${cont};
    mkdir -p "$INFO_DIR";
    (
        if [ "${engine}" = 'docker' ]; then
            ${engine} top "$cont" auxw;
        # NOTE(cjeanner): `podman top` does not support `ps` options.
        elif [ "${engine}" = 'podman' ]; then
            ${engine} top "$cont";
        fi
        ${engine} exec "$cont" vmstat -s
        ${engine} exec "$cont" ps axfo %mem,size,rss,vsz,pid,args
        ${engine} exec -u root "$cont" bash -c "\$(command -v dnf || command -v yum) list installed";
    ) &>> "$INFO_DIR/${engine}_info.log";

    container_cp "$cont" /var/lib/kolla/config_files/config.json "$INFO_DIR/config.json";

    # Capture rpms updated from more recent repos
    update_repos="gating delorean-current"
    if ls /etc/yum.repos.d/*-component.repo 1> /dev/null 2>&1; then
        component_name=$(cat /etc/yum.repos.d/*-component.repo | grep "name=" | sed "s/name=//g")
        update_repos="${update_repos} ${component_name}"
    fi
    echo "*** ${cont} rpm update info ***" >> "$BASE_CONTAINER_EXTRA/container_updates_info.log"
    for repo in $update_repos; do
        grep "@${repo}" "$INFO_DIR/${engine}_info.log" >> "$BASE_CONTAINER_EXTRA/container_updates_info.log"
    done;

    # NOTE(flaper87): This should go away. Services should be
    # using a `logs` volume
    # NOTE(mandre) Do not copy logs if the containers is bind mounting /var/log directory
    if ! ${engine} inspect "$cont" | jq .[0].Mounts[].Source | grep -x  '"/var/log[/]*"' >/dev/null 2>&1; then
            container_cp "$cont" /var/log "$INFO_DIR/log";
    fi;

    # Delete symlinks because they break log collection and are generally
    # not useful
    find "$INFO_DIR" -type l -delete;
done;

# NOTE(cjeanner) previous loop cannot have the "-a" flag because of the
# "exec" calls. So we just loop a second time, over ALL containers,
# in order to get all the logs we can. For instance, the previous loop
# would not allow to know why a container is "Exited (1)", preventing
# efficient debugging.
for cont in $(${engine} ps -a | awk '{print $NF}' | grep -v NAMES); do
    INFO_DIR=$BASE_CONTAINER_EXTRA/containers/${cont};
    mkdir -p "$INFO_DIR";
    ${engine} logs "$cont" &> "$INFO_DIR/stdout.log";
done;

# NOTE(flaper87) Copy contents from the logs volume. We can expect this
# volume to exist in a containerized environment.
# NOTE(cjeanner): Rather test the eXistenZ of the volume, as podman does not
# have such thing
if [ -d /var/lib/docker/volumes/logs/_data ]; then
    cp -r /var/lib/docker/volumes/logs/_data "$BASE_CONTAINER_EXTRA/logs";
fi
