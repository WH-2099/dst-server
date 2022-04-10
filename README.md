# 饥荒专服 Docker 镜像
[<img src="https://cdn.akamai.steamstatic.com/steam/apps/322330/header_schinese.jpg?t=1643303985" alt="STEAM 商店头图" align="center"/>](https://store.steampowered.com/app/322330/)
## 偏好核对
**强烈建议使用前先检查本项目是否能满足您的偏好。**
- [ ] 饥荒联机版（Don't Starve Together）
- [ ] 专用服务器（Dedicated Server）
- [ ] Docker 镜像（Docker image）
- [ ] STEAM 平台（Steam platform）
- [ ] 64 位 Linux 系统（64-bit Linux System）
- [ ] **极简纯净（[KISS原则](https://zh.wikipedia.org/wiki/KISS%E5%8E%9F%E5%88%99)）**
- [ ] 遵循官方规范（[Official Specifications](#官方规范)）

## 安装
**此部分尚未完成**
1. 请确保已经安装了 [Docker 引擎](https://docs.docker.com/engine/)
   - 如果没有安装，可参照官网指导 [Install Docker Engine](https://docs.docker.com/engine/install/)
2. 创建需要的配置文件夹
2. 拉取镜像并启动容器
   #TODO: docker compose 直接启动双世界
   - 在命令行中运行 `docker run --name dst-master --restart unless-stopped -v "${HOME}"/DST:/data/conf --network host wh2099/dst-docker`
       - 游戏存档目录默认为 `"${HOME}"/DST` ，可根据需要自行修改 
       - 推荐直接配置 `--network host`，毕竟理论上网络性能会好那么一丢丢（安全性就相信一次 Klei 吧）


## 动机
个人长期使用 GitHub 上的相关项目，不甚满意。

本身简简单单几行能搞定的小项目，非要拆一堆变量出来，再多搞几层调用。

大项目这么搞是规范，但对于核心代码不超 20 行的小项目，**过犹不及**。

说是遵循规范吧，不用 V 社给的 steamcmd 的官方 docker 镜像，还把游戏服务端本体内容打进 Docker。。。。。。

最后搞得项目一堆小文件，生成的 Docker 镜像 1G 多，即便如此还是躲不开 STEAM 和游戏更新，何苦呢？

Klei 都主动升级 64 位客户端了，默认启动仍是 32 位。。。。。。

游戏里咱就是纯净强迫症患者，于是参照官方规范做一个 Docker 镜像。

## 配置文件
**专服配置文件结构及变量含义，注释中的赋值均为默认值。**
```
Cluster_1  # 以集群方式提供服务，地面和洞穴是两个独立的服务器进程
├── cluster.ini  # 集群配置
├── cluster_token.txt  # 集群认证码
├── adminlist.txt  # 管理员名单，克雷的 ID（KU_XXXXXXXX），一行一个
├── blocklist.txt  # 封禁名单，SteamID64，一行一个
├── whitelist.txt  # 特权名单，克雷的 ID（KU_XXXXXXXX），一行一个
├── Master  # 主服务器进程（地面）
│   ├── server.ini  # 服务器配置
│   ├── modoverrides.lua  # mod 的设置
│   ├── leveldataoverride.lua  # 世界（地形、生物等）的设置
│   └── save  # 存档
│       └── ...
├── Caves  # 洞穴服务器
│   ├── server.ini  # 服务器配置
│   ├── modoverrides.lua  # mod 的设置
│   ├── leveldataoverride.lua  # 世界（地形、生物等）的设置
│   └── save  # 存档
│       └── ...
└── mods  # mod 相关
    └── dedicated_server_mods_setup.lua  # mod 加载设定
```

### cluster.ini
```
[MISC]
; 要保留的最大快照数量。
; 这些快照在每次保存时都会被创建，并在 "主机游戏 "屏幕的 "回滚 "标签中可用。
; max_snapshots = 6

; 允许在服务器运行的命令提示符或终端中输入 lua 命令。
; console_enabled = true


[SHARD]
; 启用服务器分片。
; 对于多级服务器，这必须被设置为 "true"。
; 对于单级服务器，它可以被省略。
; shard_enabled = false

; 这是主服务器将监听的网络地址，供其他分片服务器连接使用。
; 如果你的集群中的所有服务器都在同一台机器上，则将其设置为 127.0.0.1 ；
; 如果你的集群中的服务器在不同的机器上，则设置为 0.0.0.0 。
; 这只需要为主服务器设置，可以在 cluster.ini 或主服务器的 server.ini 中设置。
; 可在 server.ini 中重写
; bind_ip = 127.0.0.1

; 非主控分片在试图连接到主控分片时将使用这个 IP 地址。
; 如果集群中的所有服务器都在同一台机器上，将其设置为 127.0.0.1 。
; 可在 server.ini 中重写
; master_ip =


; 这是主服务器将监听的 UDP 端口，非主分片在试图连接到主分片时将使用这个端口。
; 这应该通过在 cluster.ini 中的条目为所有分片设置相同的值，或者完全省略以使用默认值。
; 这必须与运行在与主控分片相同机器上的任何分片上的 server_port 设置不同。
; 可在 server.ini 中重写
; master_port = 10888

; 这是一个用于验证从属服务器与主服务器的密码。
; 如果你在不同的机器上运行需要相互连接的服务器，这个值在每台机器上必须是相同的。
; 对于在同一台机器上运行的服务器，你可以只在 cluster.ini 中设置。
; 可在 server.ini 中重写
; cluster_key =


[STEAM]
; 当设置为 "true "时，服务器将只允许属于 steam_group_id 设置中指定的 steam 组的玩家连接。
; steam_group_only = false

; steam_group_only / steam_group_admins 设置相关的 steam 组 ID。
; steam_group_id = 0

; 当这个设置为 "true "时，在 steam_group_id 中指定的 steam 组的管理员也将在服务器上拥有管理员身份。
; steam_group_admins = false


[NETWORK]
; 创建一个离线集群。
; 该服务器不会被公开列出，只有本地网络上的玩家能够加入，任何与 steam 有关的功能都会失效。
; offline_cluster = false

; 这是服务器每秒钟向客户提供更新数据的次数。
; 增加这个次数可以提高精度，但会消耗更大的网络带宽。
; 建议将其保持在默认值 15 。
; 建议你只在局域网游戏中改变这个选项，并使用一个能被 60 除以的数字（15、20、30）。
; tick_rate = 15

; 为白名单上的玩家保留的空位数量。
; 要将一个玩家列入白名单，请将他们的 Klei UserId 添加到 whiteelist.txt 文件中（将此文件与 cluster.ini 放在同一个目录中）。
; 仅可用于主分片的 cluster.ini
; whitelist_slots = 0

; 这是玩家加入你的服务器时必须输入的密码。
; 留空或省略它表示没有密码。
; 仅可用于主分片的 cluster.ini
; cluster_password =

; 你的服务器集群的名称。
; 这是将显示在服务器列表中的名称。
; 仅可用于主分片的 cluster.ini
; cluster_name =

; 集群描述。
; 这将显示在 "浏览游戏 "界面中的服务器信息区域。
; 仅可用于主分片的 cluster.ini
; cluster_description =

; 当设置为 "true "时，服务器将只接受来自同一局域网内机器的连接。
; 仅可用于主分片的 cluster.ini
; lan_only_cluster = false

; 集群的游戏风格。
; 这个字段相当于 "创建游戏"界面中的 "服务器游戏风格 "字段。
; 仅可用于主分片的 cluster.ini
; 有效值如下（不包含括号及括号中内容）：
; social  （社交）
; cooperative  （合作）
; competitive  （竞争）
; madness  （疯狂）
; cluster_intention =

; 当这个选项被设置为 false 时，游戏将不再在每天结束时自动保存。
; 游戏仍然会在关机时保存，并且可以使用 c_save() 手动保存。
; autosaver_enabled = true

; 集群的语言
; 中文 zh
; cluster_language = en

[GAMEPLAY]
; 可以同时连接到集群的最大玩家数量。
; 仅可用于主分片的 cluster.ini
; max_players = 16

; 玩家间战斗（队友伤害）
; pvp = false

; 集群的游戏模式。
; 这个字段相当于 "创建游戏 "界面中的 "游戏模式 "字段。
; 有效值如下（不包含括号及括号中内容）：
; survival  （生存）
; endless  （无尽）
; wilderness  （荒野）
; game_mode = survival

; 当没有玩家连接时，暂停服务器。
; pause_when_empty = false

; 设置为 "true"，以启用投票功能。
; vote_enabled = true
```

### server.ini
```
[SHARD]
; 设置一个分片为集群的主分片。
; 每个集群必须有一个主服务器。
; 在主服务器的 server.ini 中设置为 true ;
; 在其他所有的 server.ini 中设置为 false 。
; is_master =

; 这是将在日志文件中显示的分片名称。
; 它对于主服务器来说是被忽略的，主服务器的名字总是叫 [SHDMASTER] 。
; name =

; 这个字段是为非主服务器自动生成的，并在内部用来唯一地识别一个服务器。
; 如果任何人的角色目前处于在这个服务器所管理的世界中，改变这个字段或删除它可能会产生问题。
; id =


[STEAM]
; steam 使用的内部端口。
; 请确保你在同一台机器上运行的每台服务器都是不同的。
; authentication_port = 8766

; steam 使用的内部端口。
; 请确保你在同一台机器上运行的每台服务器都是不同的。
; master_server_port = 27016


[NETWORK]
; 该服务器将监听连接的 UDP 端口。
; 如果你正在运行一个多级集群，对同一台机器上的多个服务器，这个端口各不相同。
; 这个端口必须在 10998 和 11018 之间（含），以便同一局域网的玩家在他们的服务器列表中看到它。
; 在某些操作系统上，低于 1024 的端口限制为只能特权用户使用。
; server_port = 10999
```
## 官方规范
1. [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD)
2. [Dedicated Server Quick Setup Guide - Linux](https://forums.kleientertainment.com/forums/topic/64441-dedicated-server-quick-setup-guide-linux/)
3. [Docker Reference Documentation](https://docs.docker.com/reference/)


## 开源许可证
[![GPLv3](https://www.gnu.org/graphics/gplv3-or-later.png)](https://www.gnu.org/licenses/gpl-3.0.html)