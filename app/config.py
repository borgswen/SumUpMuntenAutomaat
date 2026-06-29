import os
from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
SECRET_PATH = BASE_DIR / "secret.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes"}

config_data = _load_yaml(CONFIG_PATH)
secret_data = _load_yaml(SECRET_PATH)

PRICE_PER_COIN = float(config_data.get("price_per_coin", 1.55))
PRESET_AMOUNTS = config_data.get("preset_amounts", [5, 10, 15, 20])
USE_SIMULATOR = _env_bool("USE_SIMULATOR", bool(config_data.get("use_simulator", True)))
DATABASE_PATH = Path(config_data.get("database_path", "data/payments.sqlite"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = BASE_DIR / DATABASE_PATH

SUMUP_API_BASE = config_data.get("sumup_api_base", "https://api.sumup.com")
SUMUP_CLIENT_ID = secret_data.get("sumup_client_id") or os.getenv("SUMUP_CLIENT_ID")
SUMUP_CLIENT_SECRET = secret_data.get("sumup_client_secret") or os.getenv("SUMUP_CLIENT_SECRET")
SUMUP_REFRESH_TOKEN = secret_data.get("sumup_refresh_token") or os.getenv("SUMUP_REFRESH_TOKEN")
SUMUP_MERCHANT_EMAIL = secret_data.get("sumup_merchant_email") or os.getenv("SUMUP_MERCHANT_EMAIL")
SUMUP_CURRENCY = config_data.get("sumup_currency", "EUR")
