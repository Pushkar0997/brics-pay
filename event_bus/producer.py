"""Lightweight pub/sub standing in for Kafka/Pulsar.

In a real deployment, topics are partitioned by transaction_id so
ordering is preserved per-transaction while different transactions
process fully independently. Swap InMemoryBus for a real
producer/consumer pair without changing any caller.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict

from event_bus.schemas import TransactionEvent


class InMemoryBus:
    def __init__(self) -> None:
        self._topics: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, topic: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._topics[topic].append(queue)
        return queue

    async def publish(self, topic: str, event: TransactionEvent) -> None:
        for queue in self._topics[topic]:
            await queue.put(event)


event_bus = InMemoryBus()
TOPIC_TRANSACTION_EVENTS = "transaction-events"


async def publish_event(event: TransactionEvent) -> None:
    await event_bus.publish(TOPIC_TRANSACTION_EVENTS, event)
