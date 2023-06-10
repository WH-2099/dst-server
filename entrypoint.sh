#!/bin/bash
STEAMCMD="/home/steam/steamcmd/steamcmd.sh"
INSTALL_PATH="/home/steam/steamapps/DST"
DATA_ROOT="/data"
UGC_PATH="${DATA_ROOT}/ugc_mods"
CONF_DIR="conf"
MODS_DIR="mods"

function fail() {
    echo Error: "$@" >&2
    exit 1
}

function check_for_file() {
    if [[ ! -f "$1" ]]; then
        fail "Missing file: $1"
    fi
}

# 检测集群文件夹名
dir_num=$(find "${DATA_ROOT}/${CONF_DIR}" -mindepth 1 -maxdepth 1 -type d | wc -l)
if [[ ${dir_num} -ne 1 ]]; then
    # 文件夹不唯一
    fail "There should be one and only one folder in ${DATA_ROOT}/${CONF_DIR}"
fi
cluster=$(find "${DATA_ROOT}/${CONF_DIR}" -mindepth 1 -maxdepth 1 -type d -printf "%f")

# 检查集群必需配置文件
cluster_dir="${DATA_ROOT}/${CONF_DIR}/${cluster}"
check_for_file "${cluster_dir}/cluster.ini"
check_for_file "${cluster_dir}/cluster_token.txt"

# 确保专服特有文件夹及文件存在
touch "${cluster_dir}/adminlist.txt"
touch "${cluster_dir}/whitelist.txt"
touch "${cluster_dir}/blocklist.txt"
mkdir -p "${cluster_dir}/${MODS_DIR}"
touch "${cluster_dir}/${MODS_DIR}/modsettings.lua"

# 检测分片文件夹名
dir_num=$(find "${cluster_dir}" -mindepth 1 -maxdepth 1 -type d ! -name "${MODS_DIR}" | wc -l)
if [[ ${dir_num} -eq 0 ]]; then
    # 找不到对应文件夹
    fail "There should be at least one folder in ${cluster_dir}"
else
    shards=($(find "${cluster_dir}" -mindepth 1 -maxdepth 1 -type d ! -name "${MODS_DIR}" -printf "%f "))
fi

# 检查分片必需配置文件，自动生成 mod 安装脚本
for shard in "${shards[@]}"; do
    shard_dir="${cluster_dir}/${shard}"
    check_for_file "${shard_dir}/server.ini"
    mod_ids=($(grep -Eo "workshop-[[:digit:]]+" "${shard_dir}/modoverrides.lua" | sed "s/workshop-//"))
done
IFS=$'\n'
mod_ids=($(sort -nu <<<"${mod_ids[*]}"))
unset IFS
rm -f "${cluster_dir}/${MODS_DIR}/dedicated_server_mods_setup.lua"
for mod_id in "${mod_ids[@]}"; do
    echo "ServerModSetup(\"${mod_id}\")" >>"${cluster_dir}/${MODS_DIR}/dedicated_server_mods_setup.lua"
done

# 更新 steam 及服务端
# 临时移除 mod 目录符号连接，避免被覆写
if [[ -L "${INSTALL_PATH}/${MODS_DIR}" ]]; then
    rm -f "${INSTALL_PATH}/${MODS_DIR}"
fi
"${STEAMCMD}" \
    +@ShutdownOnFailedCommand 1 +@NoPromptForPassword 1 +force_install_dir "${INSTALL_PATH}" \
    +login anonymous +app_update 343050 validate +quit
rm -rf "${INSTALL_PATH:?}/${MODS_DIR:?}"
ln -s "${cluster_dir}/${MODS_DIR}" "${INSTALL_PATH}/${MODS_DIR}"

# 进入服务端目录
cd "${INSTALL_PATH}/bin64" || fail "Can't cd to ${INSTALL_PATH}/bin64"

# 更新 mod
# 使用临时分片文件夹，无需配置文件
# 避免服务端启动默认创建 Master 分片文件夹
temp_shard_dir=$(mktemp -dp "${cluster_dir}") || fail "Can't create temp shard dir for mod update"
trap "rm -rf ${temp_shard_dir}" EXIT
temp_shard=$(basename "${temp_shard_dir}")
./dontstarve_dedicated_server_nullrenderer_x64 \
    -only_update_server_mods \
    -monitor_parent_process $$ \
    -ugc_directory "${UGC_PATH}" \
    -persistent_storage_root "${DATA_ROOT}" \
    -conf_dir "${CONF_DIR}" \
    -cluster "${cluster}" \
    -shard "${temp_shard}" | sed -u "s/^/[MOD_UPDATE]: /"
rm -rf "${temp_shard_dir}"

# 信号处理，优雅关闭服务器
trap handle_term TERM
function handle_term() {
    killall -w -s TERM "dontstarve_dedicated_server_nullrenderer_x64"
    chown steam:steam -R "${DATA_ROOT}"
    exit 0
}

# 启动集群
for shard in "${shards[@]}"; do
    # 清除旧缓存
    rm -f "${cluster_dir}/${shard}/save/server_temp/server_save"

    # 创建 console 管道
    shard_dir="${cluster_dir}/${shard}"
    if [[ ! -p "${shard_dir}/console" ]]; then
        rm -f "${shard_dir}/console"
        mkfifo "${shard_dir}/console"
    fi
    exec 3<>"${shard_dir}/console"

    # 启动分片
    ./dontstarve_dedicated_server_nullrenderer_x64 \
        -skip_update_server_mods \
        -monitor_parent_process $$ \
        -ugc_directory "${UGC_PATH}" \
        -persistent_storage_root "${DATA_ROOT}" \
        -conf_dir "${CONF_DIR}" \
        -cluster "${cluster}" \
        -shard "${shard}" <&3 | sed -u "s/^/${shard}: /" &
done
wait
