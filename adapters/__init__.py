"""National rail adapter registry.

Adding a new BRICS or partner country means writing one adapter file
and registering it here - the core services never change."""
from __future__ import annotations

from adapters.base_adapter import NationalRailAdapter
from adapters.brazil_pix import BrazilPixAdapter
from adapters.china_cips import ChinaCipsAdapter
from adapters.india_upi import IndiaUpiAdapter
from adapters.russia_spfs import RussiaSpfsAdapter
from adapters.south_africa_rtc import SouthAfricaRtcAdapter

_REGISTRY: dict[str, NationalRailAdapter] = {
    "IN": IndiaUpiAdapter(),
    "CN": ChinaCipsAdapter(),
    "BR": BrazilPixAdapter(),
    "RU": RussiaSpfsAdapter(),
    "ZA": SouthAfricaRtcAdapter(),
}


def get_adapter(country_code: str) -> NationalRailAdapter:
    try:
        return _REGISTRY[country_code]
    except KeyError:
        raise ValueError(f"no national rail adapter registered for {country_code}")
