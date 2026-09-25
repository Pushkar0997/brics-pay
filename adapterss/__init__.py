"""
Adapter package.

`get_adapter(country)` is the one function the core (payment_router)
depends on. Adding a new country/rail means adding one file here that
implements `RailAdapter` and one line in the registry below — nothing
in the state machine, orchestrator, or any other service needs to change.
This is the whole point of the adapter pattern for this system: the rail
integrations are the part most likely to churn (new countries, rails
changing their APIs) and they're isolated to this one directory.
"""

from common.models import CountryCode

from adapters.base_adapter import RailAdapter
from adapters.india_upi import IndiaUPIAdapter
from adapters.china_cips import ChinaCIPSAdapter
from adapters.brazil_pix import BrazilPIXAdapter
from adapters.russia_spfs import RussiaSPFSAdapter
from adapters.south_africa_rtc import SouthAfricaRTCAdapter

_REGISTRY: dict[CountryCode, RailAdapter] = {
    CountryCode.INDIA: IndiaUPIAdapter(),
    CountryCode.CHINA: ChinaCIPSAdapter(),
    CountryCode.BRAZIL: BrazilPIXAdapter(),
    CountryCode.RUSSIA: RussiaSPFSAdapter(),
    CountryCode.SOUTH_AFRICA: SouthAfricaRTCAdapter(),
}


def get_adapter(country: CountryCode) -> RailAdapter:
    try:
        return _REGISTRY[country]
    except KeyError as exc:
        raise ValueError(f"No rail adapter registered for country {country}") from exc
