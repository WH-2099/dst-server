#!/usr/bin/python3

import asyncio
from collections.abc import Iterable

from models import ClusterConfig, ServerConfig
from server import Cluster, Shard


def gen_config(codes: Iterable[int]):
    for i in codes:
        Cluster.conf_dir="root"
        c = ClusterConfig()
        c.misc.max_snapshots = 10
        c.shard.shard_enabled = True
        c.shard.cluster_key = "lst"
        c.network.cluster_name = f"LST-{i:02}"
        c.network.cluster_description = (
            "Let's Starve Together! QQ群：924715341 QQ频道：饥荒联机版"
        )
        c.network.cluster_language = "zh"
        cluster = Cluster(name=str(i), config=c)

        fc = ServerConfig()
        fc.shard.is_master = True
        fc.shard.name = "forest"
        forest = Shard(cluster=cluster, name="forest", config=fc)

        cc = ServerConfig()
        cc.shard.is_master = False
        cc.shard.name = "cave"
        cave = Shard(cluster=cluster, name="cave", config=cc)

        cluster.shards.extend((forest, cave))
        cluster.auto_config(i)
        cluster.save_config()


if __name__ == "__main__":
    cluster = Cluster(name="cluster")
    cluster.load_shards()
    asyncio.run(cluster.start())
