from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import os
import yaml


@dataclass
class PaymentSimulationConfig:
    mode: str = "success"
    delay_ms: int = 2500


@dataclass
class HopperSimulationConfig:
    speed: float = 6.0
    capacity: int = 2500
    start_amount: int = 1732
    jam_probability: float = 0.0
    random_failures: bool = False


@dataclass
class SimulationConfig:
    enabled: bool = True
    payment: PaymentSimulationConfig = PaymentSimulationConfig()
    hopper: HopperSimulationConfig = HopperSimulationConfig()


@dataclass(frozen=True)
class AppConfig:
    price_per_coin: float
    preset_amounts: list[int]
    use_simulator: bool
    database_path: Path
    sumup_api_base: str
    sumup_currency: str
    simulation: SimulationConfig


@dataclass(frozen=True)
class SecretConfig:
    sumup_client_id: str | None
    sumup_client_secret: str | None
    sumup_refresh_token: str | None
    sumup_merchant_email: str | None


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config.yaml"
SECRET_PATH = BASE_DIR / "secret.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _env_override(key: str, default: Any) -> Any:
    value = os.environ.get(key)
    if value is None:
        return default
    if isinstance(default, bool):
        return value.lower() in {"1", "true", "yes", "on"}
    if isinstance(default, int):
        return int(value)
    if isinstance(default, float):
        return float(value)
    return value


def load_config() -> AppConfig:
    data = _load_yaml(CONFIG_PATH)
    simulation_data = data.get("simulation", {}) or {}

    payment_data = simulation_data.get("payment", {}) or {}
    hopper_data = simulation_data.get("hopper", {}) or {}

    simulation = SimulationConfig(
        enabled=bool(simulation_data.get("enabled", True)),
        payment=PaymentSimulationConfig(
            mode=str(payment_data.get("mode", "success")),
            delay_ms=int(payment_data.get("delay_ms", 2500)),
        ),
        hopper=HopperSimulationConfig(
            speed=float(hopper_data.get("speed", 6.0)),
            capacity=int(hopper_data.get("capacity", 2500)),
            start_amount=int(hopper_data.get("start_amount", 1732)),
            jam_probability=float(hopper_data.get("jam_probability", 0.0)),
            random_failures=bool(hopper_data.get("random_failures", False)),
        ),
    )

    return AppConfig(
        price_per_coin=float(data.get("price_per_coin", 1.55)),
        preset_amounts=list(data.get("preset_amounts", [5, 10, 15, 20])),
        use_simulator=bool(data.get("use_simulator", True)),
        database_path=Path(data.get("database_path", "data/payments.sqlite")),
        sumup_api_base=str(data.get("sumup_api_base", "https://api.sumup.com")),
        sumup_currency=str(data.get("sumup_currency", "EUR")),
        simulation=simulation,
    )


def load_secrets() -> SecretConfig:
    data = _load_yaml(SECRET_PATH)
    return SecretConfig(
        sumup_client_id=data.get("sumup_client_id"),
        sumup_client_secret=data.get("sumup_client_secret"),
        sumup_refresh_token=data.get("sumup_refresh_token"),
        sumup_merchant_email=data.get("sumup_merchant_email"),
    )
