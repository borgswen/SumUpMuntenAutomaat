from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    price_per_coin: float
    preset_amounts: list[int]
    use_simulator: bool
    database_path: Path
    sumup_api_base: str
    sumup_currency: str


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


def load_config() -> AppConfig:
    data = _load_yaml(CONFIG_PATH)
    return AppConfig(
        price_per_coin=float(data.get("price_per_coin", 1.55)),
        preset_amounts=list(data.get("preset_amounts", [5, 10, 15, 20])),
        use_simulator=bool(data.get("use_simulator", True)),
        database_path=Path(data.get("database_path", "data/payments.sqlite")),
        sumup_api_base=str(data.get("sumup_api_base", "https://api.sumup.com")),
        sumup_currency=str(data.get("sumup_currency", "EUR")),
    )


def load_secrets() -> SecretConfig:
    data = _load_yaml(SECRET_PATH)
    return SecretConfig(
        sumup_client_id=data.get("sumup_client_id"),
        sumup_client_secret=data.get("sumup_client_secret"),
        sumup_refresh_token=data.get("sumup_refresh_token"),
        sumup_merchant_email=data.get("sumup_merchant_email"),
    )
