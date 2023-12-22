import asyncio
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar

from enums import EventType
from models import (
    ClusterConfig,
    ClusterShard,
    LobbyData,
    ServerConfig,
    ServerNetwork,
    ServerSteam,
)
from service import KleiService
from utils import fd_change2, get_free_udp_port


# 进程模型
@dataclass
class Shard:
    """分片"""

    cluster: "Cluster"
    name: str = "Master"
    config: ServerConfig = field(default_factory=ServerConfig)

    @property
    def path(self) -> Path:
        """分片文件夹路径"""

        return self.cluster.path / self.name

    @property
    def ini_path(self) -> Path:
        """ini 配置文件路径"""

        return self.path / "server.ini"

    @property
    def console_path(self) -> Path:
        """控制台管道文件路径"""

        return self.path / "console"

    @property
    def modoverrides_path(self) -> Path:
        """modoverrides.lua 路径"""

        return self.path / "modoverrides.lua"

    @property
    def leveldataoverride_path(self) -> Path:
        """leveldataoverride.lua 路径"""

        return self.path / "leveldataoverride.lua"

    @property
    def server_temp_path(self) -> Path:
        """服务端临时文件路径"""

        return self.path / "save/server_temp/server_save"

    def load_config(self) -> None:
        """加载配置"""

        ini_path = self.ini_path
        if not ini_path.is_file():
            raise FileNotFoundError(ini_path)
        self.config = ServerConfig.load(ini_path)

    def save_config(self) -> None:
        """保存配置"""

        self.config.save(self.ini_path)

    async def start(
        self,
        *args: str,
        only_update_server_mods: bool = False,
        skip_update_server_mods: bool = True,
        cloudserver: bool = False,
    ) -> None:
        """启动分片"""

        cmd_list = self.cluster.cmd_list + ["-shard", self.name, *args]
        if only_update_server_mods:
            cmd_list.append("-only_update_server_mods")
        if skip_update_server_mods:
            cmd_list.append("-skip_update_server_mods")
        if cloudserver:
            cmd_list.append("-cloudserver")
            console_path = self.console_path
            if not console_path.is_fifo():
                console_path.unlink(missing_ok=True)
                os.mkfifo(console_path)
            fd3 = os.open(console_path, os.O_RDONLY)
            fd4 = os.open("fd4", os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            fd5 = os.open("fd5", os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            fd_change2(fd3, 3)
            fd_change2(fd4, 4)
            fd_change2(fd5, 5)

        self._process = await asyncio.create_subprocess_exec(
            cmd_list[0],
            *cmd_list[1:],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=False,
            cwd=self.cluster.bin_path.parent,
        )

        if cloudserver:
            os.close(3)
            os.close(4)
            os.close(5)

        await self._handle_log()

    async def stop(self) -> None:
        """停止分片"""

        if self._process:
            self._process.terminate()
            await self._process.communicate()

    async def _handle_log(self) -> None:
        """处理日志输出"""

        try:
            while True:
                stdout_bytes = await self._process.stdout.readline()
                if len(stdout_bytes) > 12:
                    # 移去开头无用的相对时间 '[00:00:11]: '
                    stdout_str = stdout_bytes[12:].decode()
                    print(f"{self.name}: {stdout_str}", end="")
                    for et in EventType:
                        if stdout_str.startswith(et):
                            # TODO:
                            ...

        except KeyboardInterrupt:
            self.stop()


@dataclass
class Cluster:
    """集群"""

    root_path: ClassVar[Path] = Path("/")
    conf_dir: ClassVar[str] = "/"
    ugc_path: ClassVar[Path] = Path("/ugc")
    install_path: ClassVar[Path] = Path("/install")
    steamcmd_path: ClassVar[Path] = Path("/home/steam/steamcmd/steamcmd.sh")
    permission_files: ClassVar[tuple[str]] = (
        "adminlist.txt",
        "whitelist.txt",
        "blocklist.txt",
    )
    bin_mapping: ClassVar[dict[int, str]] = {
        32: "bin/dontstarve_dedicated_server_nullrenderer",
        64: "bin64/dontstarve_dedicated_server_nullrenderer_x64",
    }

    name: str = "Cluster_1"
    config: ClusterConfig = field(default_factory=ClusterConfig)
    shards: list[Shard] = field(default_factory=list)
    architecture: int = 64

    @classmethod
    def update_server(cls, beta: bool = False, validate: bool = False) -> None:
        """更新服务端"""

        app_update_cmd = "+app_update 343050"
        if beta:
            app_update_cmd += " -beta updatebeta"

        steam_cmds = [
            "+@ShutdownOnFailedCommand 1",
            "+@NoPromptForPassword 1",
            f"+force_install_dir {cls.install_path}",
            "+login anonymous",
            app_update_cmd,
            "+quit",
        ]
        if validate:
            steam_cmds.insert(-1, "+validate")

        subprocess.run(
            (str(cls.steamcmd_path), *steam_cmds),
            check=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    @classmethod
    async def update_mods(cls) -> None:
        """更新模组"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cluster = cls(name=temp_path.name)
            shard = Shard(cluster=cluster)
            free_udp_port = get_free_udp_port()
            await shard.start(
                "-steam_master_server_port",
                str(free_udp_port),
                "-steam_authentication_port",
                str(free_udp_port + 1),
                only_update_server_mods=True,
                skip_update_server_mods=False,
            )

    @property
    def path(self) -> Path:
        """集群文件夹路径"""

        return self.root_path / self.conf_dir / self.name

    @property
    def ini_path(self) -> Path:
        """ini 配置文件路径"""

        return self.path / "cluster.ini"

    @property
    def bin_path(self) -> Path:
        """服务端可执行文件路径"""

        return self.install_path / self.bin_mapping[self.architecture]

    @property
    def cmd_list(self) -> list[str]:
        """命令列表"""

        return [
            str(self.bin_path),
            "-monitor_parent_process",
            str(os.getpid()),
            "-persistent_storage_root",
            str(self.root_path),
            "-conf_dir",
            self.conf_dir,
            "-ugc_directory",
            str(self.ugc_path),
            "-cluster",
            self.name,
        ]

    @property
    def master_shard(self) -> None | Shard:
        """主分片"""

        for shard in self.shards:
            if shard.config.shard.is_master:
                break
        else:
            shard = None

        return shard

    def load_config(self, include_shards: bool = True) -> None:
        """加载配置"""

        ini_path = self.ini_path
        if not ini_path.is_file():
            raise FileNotFoundError(ini_path)
        self.config = ClusterConfig.load(ini_path)

        if include_shards:
            for shard in self.shards:
                shard.load_config()

    def save_config(self, include_shards: bool = True) -> None:
        """保存配置"""

        self.config.save(self.ini_path)

        if include_shards:
            for shard in self.shards:
                shard.save_config()

    def load_shards(self) -> list[Shard]:
        """加载分片"""

        for p in filter(lambda p: p.is_dir(), self.path.iterdir()):
            shard = Shard(cluster=self, name=p.name)
            self.shards.append(shard)

    def auto_config(self, cluster_offset: int = 1) -> None:
        """配置端口
        针对经典一主一从的架构
        """

        default_master_port = ClusterShard().master_port
        self.config.shard.master_port = default_master_port - cluster_offset

        default_server_steam = ServerSteam()
        default_steam_auth_port = default_server_steam.authentication_port
        default_steam_server_port = default_server_steam.master_server_port

        default_shard_port = ServerNetwork().server_port

        for i, shard in enumerate(
            # 确保主分片在最前
            sorted(self.shards, key=lambda s: s.config.shard.is_master, reverse=True),
        ):
            abs_offset = cluster_offset + i
            if shard.config.shard.is_master:
                offset = +abs_offset
            else:
                offset = -abs_offset

            c = shard.config
            c.shard.id = abs_offset
            base_name, *_ = c.shard.name.partition("-")
            c.shard.name = f"{base_name}-{abs_offset}"

            c.steam.authentication_port = default_steam_auth_port + offset
            c.steam.master_server_port = default_steam_server_port + offset
            c.network.server_port = default_shard_port + 1 + offset

    def ensure_files(self) -> None:
        """确保文件齐全"""

        for file_name in self.permission_files:
            file_path = self.path / file_name
            file_path.touch()

    async def start(self) -> None:
        """启动集群"""

        self.ensure_files()
        async with asyncio.TaskGroup() as tg:
            for shard in self.shards:
                tg.create_task(shard.start())

    async def _get_lobby_data(self) -> None | LobbyData:
        """获取对应的大厅数据"""

        async with KleiService() as ks:
            data_list = await ks.get_lobby_data()

        for data in data_list:
            if (
                # 粗略匹配即可
                data.name == self.config.network.cluster_name
                and data.port == self.master_shard.config.network.server_port
            ):
                break
        else:
            data = None

        return data

    async def stop(self) -> None:
        """停止集群"""

        async with asyncio.TaskGroup() as tg:
            for shard in self.shards:
                tg.create_task(shard.stop())
