from __future__ import annotations

import os
from typing import Optional


def _is_colab() -> bool:
    """
    Detect whether we are running inside Google Colab.
    This is safe and does NOT import google.colab unless it exists.
    """
    try:
        import google.colab  # type: ignore
        return True
    except Exception:
        return False


def read_colab_userdata_or_env(key: str) -> Optional[str]:
    """
    Read a secret value in a platform-agnostic way.

    Resolution order:
      1) Google Colab userdata (if running in Colab)
      2) Environment variable

    No side effects:
      - does NOT set os.environ
      - does NOT mutate global state
      - safe to call anywhere
    """
    # 1) Google Colab
    if _is_colab():
        try:
            from google.colab import userdata  # type: ignore
            value = userdata.get(key)
            if value:
                return value
        except Exception:
            # Fall through to env
            pass

    # 2) Environment variable
    return os.getenv(key)