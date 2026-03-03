import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".ollamatermui" / "config.json"
DEFAULT_CONFIG = {
  "ollama_url": "http://192.168.1.200:11434",
  "system_prompt": "",
}


def load_config() -> dict:
  try:
    if CONFIG_PATH.exists():
      with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
      return {**DEFAULT_CONFIG, **data}
  except Exception:
    pass
  return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
  try:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
      json.dump(config, f, indent=2)
  except Exception:
    pass
