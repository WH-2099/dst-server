from abc import ABC
from configparser import ConfigParser
from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter, field_validator

from enums import OnewordType, Platform, Region, Role, Season
from utils import lua_table_to_list


# 数据模型
class Player(BaseModel):
    """玩家"""

    name: str
    kuid: None | str = None
    prefab: None | Role = None
    netid: None | int = None
    ip: None | IPv4Address = None


class Secondary(BaseModel):
    """次级分片信息"""

    id: str
    port: None | int = None
    addr: None | Annotated[IPv4Address, Field(alias="__addr")] = None
    steamid: None | str = None


class LobbyData(BaseModel, populate_by_name=True):
    """大厅数据"""

    row_id: Annotated[str, Field(alias="__rowId")]
    name: str
    addr: Annotated[IPv4Address, Field(alias="__addr")]
    port: int
    host: str
    connected: int
    maxconnections: int
    v: int
    allownewplayers: bool
    clanonly: bool
    clienthosted: bool
    dedicated: bool
    fo: bool
    lanonly: bool
    mods: bool
    password: bool
    pvp: bool
    serverpaused: bool
    platform: Platform
    session: str
    guid: str
    intent: str
    steamroom: str
    region: Region  # 这个是额外添加的非接口字段

    tags: None | str = None
    mode: None | str = None
    season: None | Season = None
    steamid: None | str = None
    secondaries: None | dict[str, Secondary] = None

    @property
    def connect_code(self) -> str:
        return f"c_connect('{self.addr}', {self.port})"


class RoomData(LobbyData):
    """房间数据"""

    tick: int
    clientmodsoff: bool
    nat: int
    data: None | str = None
    worldgen: None | str = None
    mods_info: None | list[None | str | bool] = None
    desc: None | str = None
    players: None | str = None
    players: Annotated[list[Player], Field(default_factory=list)]

    @field_validator("players", mode="plain")
    @classmethod
    def validate_players(cls, v: None | str) -> list[Player]:
        """解析玩家数据字符串"""
        players = []
        if v:
            d = lua_table_to_list(v)
            players = TypeAdapter(list[Player]).validate_python(d)

        return players


class Oneword(BaseModel, populate_by_name=True):
    """一言"""

    id: int
    uuid: UUID
    word: Annotated[str, Field(alias="hitokoto")]
    type: OnewordType
    from_: Annotated[str, Field(alias="from")]
    from_who: None | str
    creator: str
    creator_uid: int
    reviewer: int
    commit_from: str
    created_at: datetime


# 配置模型
class ClusterMisc(BaseModel):
    """集群杂项配置"""

    max_snapshots: int = 6
    console_enabled: bool = True


class ClusterShard(BaseModel):
    """集群分片配置"""

    shard_enabled: bool = False
    bind_ip: IPv4Address = IPv4Address("127.0.0.1")
    master_ip: IPv4Address = IPv4Address("127.0.0.1")
    master_port: int = 10888
    cluster_key: str = "defaultPass"


class ClusterSteam(BaseModel):
    """集群 Steam 配置"""

    steam_group_only: bool = False
    steam_group_id: int = 0
    steam_group_admins: bool = False


class ClusterNetwork(BaseModel):
    """集群网络配置"""

    cluster_name: str = ""
    cluster_password: str = ""
    cluster_description: str = ""
    tick_rate: int = 15
    offline_cluster: bool = False
    lan_only_cluster: bool = False
    autosaver_enabled: bool = True
    whitelist_slots: int = 0
    cluster_language: str = "en"


class ClusterGameplay(BaseModel):
    """集群游戏配置"""

    max_players: int = 16
    pvp: bool = False
    pause_when_empty: bool = True
    vote_enabled: bool = True


class ServerShard(BaseModel):
    """服务端分片配置"""

    is_master: bool = True
    name: str = "[SHDMASTER]"
    id: int = 1


class ServerSteam(BaseModel):
    """服务端 Steam 配置"""

    authentication_port: int = 8766
    master_server_port: int = 27016


class ServerNetwork(BaseModel):
    """服务端网络配置"""

    server_port: int = 10999


class ServerAccount(BaseModel):
    """服务端账户配置"""

    encode_user_path: bool = False


class IniModel(BaseModel, ABC):
    @classmethod
    def load(cls, ini_path: Path) -> Self:
        """加载 ini 配置"""

        parser = ConfigParser()
        with ini_path.open(mode="r", encoding="utf-8") as f:
            parser.read_file(f)
        config_dict = {
            section: {k: v for k, v in parser.items(section) if v is not None}
            for section in parser.sections()
        }
        return cls.model_validate(config_dict)

    def save(self, ini_path: Path) -> None:
        """保存 ini 配置"""

        config_dict = self.model_dump()

        # 值 True 会被解析成 false
        # 在这个地方折磨了近十个小时才发现。。。
        for section_dict in config_dict.values():
            for k, v in section_dict.items():
                if isinstance(v, bool):
                    section_dict[k] = str(v).lower()

        parser = ConfigParser()
        parser.read_dict(config_dict)
        ini_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        with ini_path.open(mode="w", encoding="utf-8") as f:
            parser.write(f)


class ClusterConfig(IniModel):
    """集群配置（cluster.ini）"""

    misc: ClusterMisc = Field(default_factory=ClusterMisc)
    shard: ClusterShard = Field(default_factory=ClusterShard)
    steam: ClusterSteam = Field(default_factory=ClusterSteam)
    network: ClusterNetwork = Field(default_factory=ClusterNetwork)
    gameplay: ClusterGameplay = Field(default_factory=ClusterGameplay)


class ServerConfig(IniModel):
    """服务端配置（server.ini）"""

    shard: ServerShard = Field(default_factory=ServerShard)
    steam: ServerSteam = Field(default_factory=ServerSteam)
    network: ServerNetwork = Field(default_factory=ServerNetwork)
    account: ServerAccount = Field(default_factory=ServerAccount)
