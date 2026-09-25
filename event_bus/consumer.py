"""Example independent consumer — reconciliation.

Run as its own process/pod so it scales and fails independently of
the payment path.
"""
from __future__ import annotations

import asyncio
import logging

from event_bus.producer import TOPIC_TRANSACTION_EVENTS, event_bus

logger = logging.getLogger("reconciliation-consumer")


async def run_reconciliation_consumer() -> None:
    queue = event_bus.subscribe(TOPIC_TRANSACTION_EVENTS)
    while True:
        event = await queue.get()
        logger.info("reconciling %s: %s", event.transaction_id, event.event_type)
        # TODO: write to the audit/analytics store


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_reconciliation_consumer())
