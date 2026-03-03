import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".ollamatermui" / "config.json"
DEFAULT_CONFIG = {
  "servers": [{"name": "192.168.1.200:11434", "url": "http://192.168.1.200:11434", "system_prompt": ""}],
  "active_server_name": "192.168.1.200:11434",
}


def _migrate_config(data: dict) -> dict:
  """Migrate old config formats to current per-server system_prompt format."""
  # Old single-URL format → create server list
  if "servers" not in data and "ollama_url" in data:
    url = data.pop("ollama_url")
    name = url.replace("http://", "").replace("https://", "").split("/")[0]
    system_prompt = data.pop("system_prompt", "")
    data["servers"] = [{"name": name, "url": url, "system_prompt": system_prompt}]
    data["active_server_name"] = name
  # Multi-server format without per-server system_prompt → move top-level into each server
  elif "servers" in data:
    top_level_prompt = data.pop("system_prompt", "")
    for server in data["servers"]:
      if "system_prompt" not in server:
        server["system_prompt"] = top_level_prompt
  return data


def load_config() -> dict:
  try:
    if CONFIG_PATH.exists():
      with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
      data = _migrate_config(data)
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
