from asyncio import Semaphore, TaskGroup
from collections.abc import Iterable
from datetime import date, datetime
from itertools import chain, product
from logging import getLogger
from types import TracebackType
from typing import NamedTuple, Self

from aiohttp import ClientError, ClientSession, TCPConnector, request
from bs4 import BeautifulSoup
from pydantic import ValidationError

from enums import OnewordType, Platform, Region, VersionType
from models import LobbyData, Oneword, RoomData

logger = getLogger(__name__)


class Version(NamedTuple):
    """游戏版本"""

    number: int
    type: VersionType
    date: date


class KleiService:
    REGION_URL = "https://lobby-v2-cdn.klei.com/regioncapabilities-v2.json"
    VERSION_URL = "https://forums.kleientertainment.com/game-updates/dst"
    BUILD_URL = "https://s3.amazonaws.com/dstbuilds/builds.json"
    LOBBY_URL = "https://lobby-v2-cdn.klei.com/{region}-{platform}.json.gz"
    ROOM_URL = "https://lobby-v2-{region}.klei.com/lobby/read"

    def __init__(self, token: None | str = None, pool_size: int = 500) -> None:
        self.session = ClientSession(
            connector=TCPConnector(limit=pool_size), raise_for_status=True
        )
        self.token = token

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: None | type[BaseException],
        exc_val: None | BaseException,
        exc_tb: None | TracebackType,
    ) -> None:
        await self.close()

    async def close(self):
        await self.session.close()

    async def get_latest_version_number(self, version_type: str = "release") -> int:
        """获取最新版本号，备用接口，不推荐"""

        async with self.session.get(self.BUILD_URL) as resp:
            data = await resp.json()
        return int(max(data[version_type], key=int))

    async def get_latest_versions(self) -> list[Version]:
        """获取最新版本数据"""

        async with self.session.get(self.VERSION_URL) as resp:
            html = BeautifulSoup(await resp.read(), "html.parser")

        versions = []
        for li in html.select("li.cCmsRecord_row"):
            number_str, type_str, date_str, *_ = li.stripped_strings
            versions.append(
                Version(
                    int(number_str),
                    VersionType(type_str),
                    datetime.strptime(date_str[9:17], "%m/%d/%y").date(),
                )
            )
        return versions

    async def get_regions(self) -> list[str]:
        """获取支持区域"""

        async with self.session.get(self.REGION_URL) as resp:
            data = await resp.json()
        return [r["Region"] for r in data["LobbyRegions"]]

    async def _get_single_lobby(
        self,
        region: Region,
        platform: Platform,
        semaphore: Semaphore,
        retry: int = 3,
    ) -> list[LobbyData]:
        """获取单个大厅数据，带重试"""

        async with semaphore:
            url = self.LOBBY_URL.format(region=region, platform=platform.name)
            raw_data = {}
            for i in range(retry + 1):
                try:
                    async with self.session.get(url) as resp:
                        raw_data = await resp.json()
                    break
                except ClientError:
                    logger.debug(f"{url} retry {i+1}")
            else:
                logger.error(f"can't get lobby data from {url}")

            data_list = []
            for d in raw_data.get("GET", []):
                d["region"] = region  # 补充接口数据未包含的地区信息
                try:
                    data_list.append(LobbyData.model_validate(d))
                except ValidationError as exc:
                    logger.debug(str(exc))
                    continue

            return data_list

    async def get_lobby_data(
        self,
        regions: Iterable[Region] = Region,
        platforms: Iterable[Platform] = Platform,
    ) -> list[LobbyData]:
        """获取游戏大厅中的房间"""

        sem = Semaphore(20)
        tasks = set()
        async with TaskGroup() as tg:
            for region, platform in product(regions, platforms):
                tasks.add(tg.create_task(self._get_single_lobby(region, platform, sem)))

        return list(chain.from_iterable(t.result() for t in tasks))

    async def _get_single_room(
        self, row_id: str, region: Region, semaphore: Semaphore, retry: int = 3
    ) -> None | RoomData:
        """获取单个房间数据，带重试"""

        async with semaphore:
            url = self.ROOM_URL.format(region=region)
            post_data = {
                "__gameId": "DontStarveTogether",
                "__token": self.token,
                "query": {"__rowId": row_id},
            }
            raw_data = {}
            for i in range(retry + 1):
                try:
                    async with self.session.post(url, json=post_data) as resp:
                        raw_data = await resp.json()
                    break
                except ClientError:
                    logger.debug(f"{row_id} retry {i+1}")
            else:
                logger.debug(f"can't get room data for {row_id}")

            data = None
            if __data := raw_data.get("GET"):
                _data = __data[0]
                _data["region"] = region
                try:
                    data = RoomData.model_validate(_data)
                except ValidationError as exc:
                    logger.debug(str(exc))

            return data

    async def get_room_data(
        self, rooms: None | Iterable[tuple[str, Region]] = None
    ) -> list[RoomData]:
        """获取房间信息"""

        if rooms is None:
            lobby_data_list = await self.get_lobby_data()
            rooms = ((d.row_id, d.region) for d in lobby_data_list)

        sem = Semaphore(10000)
        tasks = set()
        async with TaskGroup() as tg:
            for room in rooms:
                tasks.add(tg.create_task(self._get_single_room(*room, sem)))
        data_list = []
        for t in tasks:
            if result := t.result():
                data_list.append(result)
        return data_list


class OnewordService:
    CN_URL = "https://v1.hitokoto.cn"
    INTERNATIONAL_URL = "https://international.v1.hitokoto.cn"

    @classmethod
    async def get_oneword(
        cls, types: None | Iterable[OnewordType] = None, retry: int = 3
    ) -> Oneword:
        params = None
        if types:
            params = [("c", t) for t in types]

        for i in range(retry + 1):
            try:
                async with request("GET", cls.CN_URL, params=params) as resp:
                    data_bytes = await resp.read()
                break
            except ClientError as exc:
                last_exc = exc
                logger.debug(f"oneword retry {i+1}")
        else:
            logger.error("can't get oneword")
            raise last_exc

        return Oneword.model_validate_json(data_bytes)

    @classmethod
    async def get_oneword_str(
        cls, types: None | Iterable[OnewordType] = None, retry: int = 3
    ) -> str:
        oneword = await cls.get_oneword(types=types, retry=retry)
        msg = f"{oneword.word}\n——《{oneword.from_}》"
        if fw := oneword.from_who:
            msg += fw
        return msg


async def test():
    from logging import DEBUG, basicConfig
    from pprint import pp
    from sys import argv

    basicConfig(level=DEBUG)

    token = argv[1]
    async with KleiService(token) as ks:
        pp(await ks.get_regions())
        pp(await ks.get_latest_version_number())
        pp(await ks.get_latest_version())
        room_data_list = await ks.get_room_data(
            (d.row_id, d.region)
            for d in filter(
                lambda x: x.host == "KU_WRv6AVc8",
                await ks.get_lobby_data((Region.AP_EAST,), (Platform.Steam,)),
            )
        )
        pp(
            [
                d.model_dump(
                    include=(
                        "row_id",
                        "name",
                        "addr",
                        "port",
                        "connected",
                        "maxconnected",
                        "season",
                        "players",
                        "data",
                    )
                )
                for d in room_data_list
            ]
        )


if __name__ == "__main__":
    from asyncio import run

    run(test())
