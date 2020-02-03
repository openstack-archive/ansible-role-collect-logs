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
    ${engine} cp ${1}:${2} $3
};

engine=$(get_engine)
echo "${engine} was detected."
BASE_CONTAINER_EXTRA=/var/log/extra/${engine};
mkdir -p $BASE_CONTAINER_EXTRA;
ALL_FILE=$BASE_CONTAINER_EXTRA/${engine}_allinfo.log;

CONTAINER_INFO_CMDS=(
    "${engine} ps --all --size"
    "${engine} images"
    "${engine} version"
    "${engine} info"
    "${engine} volume ls"
);

for cmd in "${CONTAINER_INFO_CMDS[@]}"; do
    echo "+ $cmd" >> $ALL_FILE;
    $cmd >> $ALL_FILE;
    echo "" >> $ALL_FILE;
    echo "" >> $ALL_FILE;
done;

# Get only failed containers, in a dedicated file
${engine} ps -a | grep -vE ' (IMAGE|Exited \(0\)|Up) ' &>> /var/log/extra/failed_containers.log;

for cont in $(${engine} ps | awk {'print $NF'} | grep -v NAMES); do
    INFO_DIR=$BASE_CONTAINER_EXTRA/containers/${cont};
    mkdir -p $INFO_DIR;
    (
        if [ ${engine} = 'docker' ]; then
            ${engine} top $cont auxw;
        # NOTE(cjeanner): `podman top` does not support `ps` options.
        elif [ ${engine} = 'podman' ]; then
            ${engine} top $cont;
        fi
        ${engine} exec $cont top -bwn1;
        ${engine} exec $cont bash -c "\$(command -v dnf || command -v yum) list installed";
        ${engine} inspect $cont;
    ) &> $INFO_DIR/${engine}_info.log;

    container_cp $cont /var/lib/kolla/config_files/config.json $INFO_DIR/config.json;

    # NOTE(flaper87): This should go away. Services should be
    # using a `logs` volume
    # NOTE(mandre) Do not copy logs if the containers is bind mounting /var/log directory
    if ! ${engine} inspect $cont | jq .[0].Mounts[].Source | grep -x  '"/var/log[/]*"' 2>1 > /dev/null; then
            container_cp $cont /var/log $INFO_DIR/log;
    fi;

    # Delete symlinks because they break log collection and are generally
    # not useful
    find $INFO_DIR -type l -delete;
done;

# NOTE(cjeanner) previous loop cannot have the "-a" flag because of the
# "exec" calls. So we just loop a second time, over ALL containers,
# in order to get all the logs we can. For instance, the previous loop
# would not allow to know why a container is "Exited (1)", preventing
# efficient debugging.
for cont in $(${engine} ps -a | awk {'print $NF'} | grep -v NAMES); do
    INFO_DIR=$BASE_CONTAINER_EXTRA/containers/${cont};
    mkdir -p $INFO_DIR;
    ${engine} logs $cont &> $INFO_DIR/stdout.log;
done;

# NOTE(flaper87) Copy contents from the logs volume. We can expect this
# volume to exist in a containerized environment.
# NOTE(cjeanner): Rather test the eXistenZ of the volume, as podman does not
# have such thing
if [ -d /var/lib/docker/volumes/logs/_data ]; then
    cp -r /var/lib/docker/volumes/logs/_data $BASE_CONTAINER_EXTRA/logs;
fi
