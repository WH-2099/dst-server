#!/usr/bin/env bash
# steam 更新
/home/steam/steamcmd/steamcmd.sh +@ShutdownOnFailedCommand 1 +@NoPromptForPassword 1 +force_install_dir "/home/steam/steamapps/DST" +login anonymous +app_update 343050 validate +quit
# 启动 64 位服务端
if [[ ! -p "/data/conf/Cluster_1/$1/console" ]]; then
    mkfifo "/data/conf/Cluster_1/$1/console"
fi
cat <&/dev/stdin >"/data/conf/Cluster_1/$1/console"
sleep infinity >"/data/conf/Cluster_1/$1/console" &
exec /home/steam/steamapps/DST/bin64/edicated_server_nullrenderer_x64 -cluster "Cluster_1" -shard "$1" -persistent_storage_root "/data" -bin64/dontstarve_dconf_dir "conf" -ugc_directory "/data/ugc_mods"
