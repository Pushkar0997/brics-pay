"""Partitioned append-only ledger.

Backed here by an in-memory dict-of-lists keyed by partition -
representing what would be a distributed database (e.g. a
Spanner/CockroachDB-style store) with one range per partition in
production."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from services.settlement_ledger.partitioning import partition_index, shard_key


@dataclass(frozen=True)
class LedgerEntry:
    transaction_id: str
    payer_country: str
    payee_country: str
    send_amount: Decimal
    send_currency: str
    receive_amount: Decimal
    receive_currency: str


class Ledger:
    def __init__(self, num_partitions: int = 16) -> None:
        self.num_partitions = num_partitions
        self._partitions: dict[int, list[LedgerEntry]] = {i: [] for i in range(num_partitions)}

    def append(self, entry: LedgerEntry) -> int:
        shard = shard_key(entry.payer_country)
        partition = partition_index(shard, self.num_partitions)
        self._partitions[partition].append(entry)
        return partition

    def entries_in_partition(self, partition: int) -> list[LedgerEntry]:
        return self._partitions[partition]


ledger = Ledger()
