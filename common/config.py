"""Per-service configuration, populated from the environment.

In production this would be seeded/refreshed by the control plane
rather than hardcoded env vars — see control_plane/policy_store.py.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str
    region: str
    control_plane_url: str
    event_bus_backend: str  # "memory" | "kafka" (kafka not implemented here)


def load_settings(service_name: str) -> Settings:
    return Settings(
        service_name=service_name,
        region=os.environ.get("BRICS_REGION", "ap-south-1"),
        control_plane_url=os.environ.get("CONTROL_PLANE_URL", "http://control-plane:8000"),
        event_bus_backend=os.environ.get("EVENT_BUS_BACKEND", "memory"),
    )
