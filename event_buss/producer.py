"""
Event bus producer.

STUB: this is an in-process, in-memory pub/sub (a dict of topic ->
subscriber callbacks). It works for the single-process demo where
payment_router and its reconciliation consumer share a Python process
(see event_bus/consumer.py), but it does NOT survive a process restart
and does NOT work across the service boundaries that exist once each
`services/*` app runs as its own container.

PRODUCTION SWAP-IN: Kafka or Pulsar.
    - `publish()` becomes `producer.send(topic, value=event.model_dump_json())`
      (confluent-kafka / aiokafka) or `producer.send(topic, event.SerializeToString())`
      (Pulsar with a protobuf schema).
    - Partition key should be `transaction_id` so all events for one
      transaction land on the same partition and are consumed in order.
    - Delivery should be `acks=all` and idempotent-producer mode enabled,
      since a duplicated *event* is far cheaper to deal with (idempotent
      consumers) than a *lost* event (a state transition nobody heard
      about, which is the failure mode that turns into unreconciled
      money in a payments system).
    - Topic name: event_bus/schemas.py:TOPIC_TRANSACTION_EVENTS, which
      should map 1:1 to a real Kafka topic name so the constant doesn't
      drift from the deployed topic.
"""

import logging
import uuid
from collections import defaultdict
from typing import Callable

from event_bus.schemas import TOPIC_TRANSACTION_EVENTS, TransactionEvent

logger = logging.getLogger("event_bus.producer")

Subscriber = Callable[[TransactionEvent], None]


class InProcessEventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Subscriber) -> None:
        self._subscribers[topic].append(callback)
        logger.info("subscriber registered on topic=%s", topic)

    def publish(self, event: TransactionEvent, topic: str = TOPIC_TRANSACTION_EVENTS) -> None:
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        logger.info(
            "event published topic=%s txn=%s %s -> %s",
            topic, event.transaction_id, event.previous_state, event.new_state,
        )
        for callback in self._subscribers.get(topic, []):
            try:
                callback(event)
            except Exception:  # noqa: BLE001 - a broken consumer must never break the publisher
                logger.exception("subscriber raised while handling event %s", event.event_id)


# Process-wide singleton for the demo.
event_bus = InProcessEventBus()


def publish_transition(
    transaction_id: str,
    idempotency_key: str,
    previous_state,
    new_state,
    payer_country: str,
    payee_country: str,
    detail: dict | None = None,
) -> TransactionEvent:
    """Convenience wrapper used by the payment router at each transition."""
    event = TransactionEvent(
        event_id=str(uuid.uuid4()),
        transaction_id=transaction_id,
        idempotency_key=idempotency_key,
        previous_state=previous_state,
        new_state=new_state,
        payer_country=payer_country,
        payee_country=payee_country,
        detail=detail or {},
    )
    event_bus.publish(event)
    return event
