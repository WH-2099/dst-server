#!/usr/bin/env bash
STEAMCMD="/home/steam/steamcmd/steamcmd.sh"
INSTALL_DIR="/home/steam/steamapps/DST"
SERVER="${INSTALL_DIR}/bin64/dontstarve_dedicated_server_nullrenderer_x64"
DATA_ROOT="/data"
UGC_PATH="${DATA_ROOT}/ugc_mods"
CONF="conf"
MOD="mods"

function fail()
{
	echo Error: "$@" >&2
	exit 1
}

function check_for_file()
{
	if [[ ! -f "$1" ]]; then
		fail "Missing file: $1"
	fi
}

# 检测集群文件夹名
dir_num=$(find ${DATA_ROOT}/${CONF} -mindepth 1 -maxdepth 1 -type d|wc -l)
if [[ $dir_num -ne 1 ]]; then
    # 文件夹不唯一
    fail "There should be one and only one folder in ${DATA_ROOT}/${CONF}"
fi
cluster=$(find ${DATA_ROOT}/${CONF} -mindepth 1 -maxdepth 1 -type d -printf "%f")

# 可手动传参指定分片，便于启动多世界集群
if [[ $# -eq 0 ]];then
    shards=("Master" "Caves")
else
    shards=("$@")
fi

# 必需配置文件
cluster_dir="${DATA_ROOT}/${CONF}/${cluster}"
check_for_file "${cluster_dir}/cluster.ini"
check_for_file "${cluster_dir}/cluster_token.txt"

# 专服特有 非必需
mkdir -p "${cluster_dir}/${MOD}"
touch "${cluster_dir}/adminlist.txt"
touch "${cluster_dir}/whitelist.txt"
touch "${cluster_dir}/blocklist.txt"
touch "${cluster_dir}/${MOD}/dedicated_server_mods_setup.lua"

# steam 更新
"${STEAMCMD}"\
    +@ShutdownOnFailedCommand 1\
    +@NoPromptForPassword 1\
    +force_install_dir "${INSTALL_DIR}"\
    +login anonymous\
    +app_update 343050 validate\
    +quit

if [[ ! -p "/data/conf/Cluster_1/$1/console" ]]; then
    mkfifo "/data/conf/Cluster_1/$1/console"
fi
cat <&/dev/stdin >"/data/conf/Cluster_1/$1/console"

# 启动 64 位服务端
for shard in "${shards[@]}"; do
    shard_dir="${cluster_dir}/${shard}"
    check_for_file "${shard_dir}/server.ini"
    "${SERVER}"\
        -ugc_directory "${UGC_PATH}"\
        -persistent_storage_root "${DATA_ROOT}"\
        -conf_dir "${CONF}"\
        -cluster "${cluster}"\
        -shard "${shard}" | sed "s/^/${shard}: /" &
done
wait


# sleep infinity >"/data/conf/Cluster_1/$1/console" &