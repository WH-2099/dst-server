#!/usr/bin/env bash

UGC_PATH="/ugc"
INSTALL_PATH="/install"
CLUSTER_PATH="/cluster"
STEAMCMD="/root/steamcmd/steamcmd.sh"

APP_ID=343050

function fail() {
    echo Error: "$@" >&2
    exit 1
}

function check_for_file() {
    if [[ ! -f "$1" ]]; then
        fail "Missing file: $1"
    fi
}

# 信号处理，优雅关闭服务器
trap handle_term TERM
function handle_term() {
    killall -ws TERM 'steamcmd' 'dontstarve_dedicated_server_nullrenderer_x64'
    exit 0
}

function get_free_port() {
    used_ports=$(ss -4tulnH | tr -s " " | cut -d" " -f5 | cut -d: -f2 | sort -nu)
    for port in {50000..60000}; do
        if ! echo "$used_ports" | grep -q "^$port$"; then
            echo "$port"
            return
        fi
        fail "Can't find a free port"
    done
}

# 用软链接保证容器间 mods 文件夹隔离
# if [[ ! -L "$INSTALL_PATH/mods" ]]; then
#     rm -rf "$INSTALL_PATH/mods"
#     ln -s "$MODS_PATH" "$INSTALL_PATH/mods"
# fi

# 更新 steam 及服务端
if [[ ! -f "$INSTALL_PATH/noupdate" ]]; then
    # Steam 会对安装路径的上层做权限判定，需要可写
    upper_install_path=$(dirname "$INSTALL_PATH")
    if [[ ! -w "$upper_install_path" ]]; then
        chmod u+w "$upper_install_path"
    fi

    "$STEAMCMD" \
        +@ShutdownOnFailedCommand 1 \
        +@NoPromptForPassword 1 \
        +force_install_dir "$INSTALL_PATH" \
        +login anonymous \
        +app_update "$APP_ID" \
        +quit
fi

# 进入服务端目录
cd "$INSTALL_PATH/bin64" || fail "can't cd to $INSTALL_PATH/bin64"

# 检测分片文件夹名
mapfile -t shards < <(find "$CLUSTER_PATH" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)

# 检查分片必需配置文件
mod_ids=()
for shard in "${shards[@]}"; do
    shard_path="$CLUSTER_PATH/$shard"
    check_for_file "$shard_path/server.ini"
    mapfile -t -O "${#mod_ids[@]}" mod_ids < <(grep -Eo "workshop-[[:digit:]]+" "$shard_path/modoverrides.lua" | sed "s/workshop-//")
done

# 更新 mod
# 使用临时分片文件夹，无需配置文件
# 避免服务端启动默认创建 Master 分片文件夹
sorted_ids=()
mapfile -t sorted_ids < <(echo "${mod_ids[@]}" | tr ' ' '\n' | sort -nu)
touch /tmp/modsettings.lua /tmp/dedicated_server_mods_setup.lua
truncate -s0 /tmp/dedicated_server_mods_setup.lua
ln -sf "/tmp/modsettings.lua" "$INSTALL_PATH/mods/modsettings.lua"
ln -sf "/tmp/dedicated_server_mods_setup.lua" "$INSTALL_PATH/mods/dedicated_server_mods_setup.lua"
for id in "${sorted_ids[@]}"; do
    echo "ServerModSetup(\"$id\")" >>"/tmp/dedicated_server_mods_setup.lua"
done

free_port=$(get_free_port)
if [[ -f "$INSTALL_PATH/proxy" ]]; then
    export http_proxy="socks5://127.0.0.1:1080"
    export https_proxy="socks5://127.0.0.1:1080"
fi

mkdir -p '/tmp/conf/c/s'
./dontstarve_dedicated_server_nullrenderer_x64 \
    -only_update_server_mods \
    -monitor_parent_process $$ \
    -steam_master_server_port "$free_port" \
    -steam_authentication_port $((free_port + 1)) \
    -ugc_directory "$UGC_PATH" \
    -persistent_storage_root '/tmp' \
    -conf_dir 'conf' \
    -cluster 'c' \
    -shard 's' | sed -u 's/^/[MOD_UPDATE]: /'
rm -rf '/tmp/conf'

unset http_proxy https_proxy

# 检查集群必需配置文件
check_for_file "$CLUSTER_PATH/cluster.ini"
check_for_file "$CLUSTER_PATH/cluster_token.txt"

# 确保专服特有文件夹及文件存在
touch "$CLUSTER_PATH/adminlist.txt"
touch "$CLUSTER_PATH/whitelist.txt"
touch "$CLUSTER_PATH/blocklist.txt"

# 启动集群
for shard in "${shards[@]}"; do
    shard_path="$CLUSTER_PATH/$shard"
    check_for_file "$shard_path/server.ini"

    # 主分片的 console 作为集群 console
    if grep -qiE 'is_master[[:space:]]*=[[:space:]]*true' "$shard_path/server.ini"; then
        console_path="$CLUSTER_PATH/console"
    else
        console_path="$shard_path/console"
    fi

    # 创建命名管道
    if [[ ! -p "$console_path" ]]; then
        rm -f "$console_path"
        mkfifo "$console_path"
    fi

    # 启动分片
    # 分片配置路径应为 <persistent_storage_root>/<conf_dir>/<cluster>/<shard>/server.ini
    # 这里的配置最终形成的路径实际为 ////clutser/shard/server.ini
    # 这在 linux 环境下等价于 /cluster/shard/server.ini
    ./dontstarve_dedicated_server_nullrenderer_x64 \
        -skip_update_server_mods \
        -monitor_parent_process $$ \
        -persistent_storage_root / \
        -conf_dir / \
        -ugc_directory "$UGC_PATH" \
        -cluster "$(basename $CLUSTER_PATH)" \
        -shard "$shard" <>"$console_path" | sed -u "s/^/$shard: /" &
    # cloudserver 模式下 TERM 后不会自动终止进程，暂时不用此模式
    # -cloudserver 3<>"$console_path" 4>>"$shard_path/fd4" 5>>"$shard_path/fd5"
done
wait
