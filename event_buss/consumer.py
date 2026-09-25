"""
Example consumer: reconciliation.

Demonstrates that the event bus decouples "things that happen to a
transaction" from "things that react to a transaction" — this consumer
knows nothing about payment_router's internals, it just watches the event
stream and keeps its own tally, the way a real reconciliation job would
compare "money the ledger says moved" against "confirmations the rails
sent back".

PRODUCTION SWAP-IN: a Kafka consumer group (`group_id="reconciliation"`)
reading TOPIC_TRANSACTION_EVENTS with `enable.auto.commit=False`, manually
committing offsets only after the reconciliation write succeeds — so a
crash mid-batch re-reads events rather than silently skipping them.
"""

import logging
from collections import Counter

from event_bus.producer import event_bus
from event_bus.schemas import TOPIC_TRANSACTION_EVENTS, TransactionEvent

logger = logging.getLogger("event_bus.consumer.reconciliation")


class ReconciliationConsumer:
    """Tracks how many transactions are currently sitting in each state."""

    def __init__(self):
        self.state_counts: Counter = Counter()
        self.completed_total = 0
        self.failed_total = 0
        self._seen_transactions: set[str] = set()

    def handle_event(self, event: TransactionEvent) -> None:
        if event.previous_state is not None:
            self.state_counts[event.previous_state] -= 1
        self.state_counts[event.new_state] += 1
        self._seen_transactions.add(event.transaction_id)

        if event.new_state == "COMPLETED":
            self.completed_total += 1
            logger.info("reconciliation: txn %s completed", event.transaction_id)
        elif event.new_state == "FAILED":
            self.failed_total += 1
            logger.warning("reconciliation: txn %s failed - %s", event.transaction_id, event.detail)

    def snapshot(self) -> dict:
        return {
            "transactions_seen": len(self._seen_transactions),
            "completed_total": self.completed_total,
            "failed_total": self.failed_total,
            "in_flight_by_state": {k: v for k, v in self.state_counts.items() if v > 0},
        }


def start_reconciliation_consumer() -> ReconciliationConsumer:
    consumer = ReconciliationConsumer()
    event_bus.subscribe(TOPIC_TRANSACTION_EVENTS, consumer.handle_event)
    logger.info("reconciliation consumer subscribed to %s", TOPIC_TRANSACTION_EVENTS)
    return consumer
