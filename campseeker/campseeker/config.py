"""Configuration loaded from the project .env without overriding exported values."""
import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env', override=False)


@dataclass(frozen=True)
class Settings:
    nps_api_key: str = field(repr=False)
    timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> 'Settings':
        key = os.getenv('NPS_API_KEY', '').strip()
        if not key:
            raise ValueError('Set NPS_API_KEY in the project .env file.')
        try:
            timeout = float(os.getenv('NPS_TIMEOUT_SECONDS', '15'))
        except ValueError:
            raise ValueError('NPS_TIMEOUT_SECONDS must be a number.') from None
        if not 1 <= timeout <= 60:
            raise ValueError('NPS_TIMEOUT_SECONDS must be between 1 and 60.')
        return cls(key, timeout)
