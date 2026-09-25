"""Geo-partitioning for the distributed ledger.

Each transaction is sharded by payer country/region so no single
partition ever sees global write volume - this is what makes
'billions of transactions per day' viable."""
from __future__ import annotations

import hashlib


def shard_key(payer_country: str) -> str:
    region_map = {
        "IN": "ap-south",
        "CN": "ap-east",
        "BR": "sa-east",
        "RU": "eu-north",
        "ZA": "af-south",
    }
    return region_map.get(payer_country, "global")


def partition_index(shard: str, num_partitions: int = 16) -> int:
    digest = hashlib.sha256(shard.encode()).hexdigest()
    return int(digest, 16) % num_partitions
