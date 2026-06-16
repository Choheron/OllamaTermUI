import requests
import json
import time

OLLAMA_BASE_URL = "http://192.168.1.200:11434"

def _base() -> str:
  return OLLAMA_BASE_URL.rstrip("/")

def check_connection(url: str) -> bool:
  """Test whether the Ollama server at the given URL is reachable."""
  try:
    response = requests.get(f"{url.rstrip('/')}/api/version", timeout=5)
    return response.ok
  except Exception:
    return False

def ping_server(url: str) -> int | None:
  """Returns round-trip latency in ms to the Ollama server, or None if unreachable."""
  try:
    start = time.monotonic()
    response = requests.get(f"{url.rstrip('/')}/api/version", timeout=5)
    if response.ok:
      return round((time.monotonic() - start) * 1000)
    return None
  except Exception:
    return None


def get_installed_models():
  # Query server for models
  response = requests.get(f"{_base()}/api/tags", timeout=10)
  modelList = response.json()['models']
  return modelList


def get_response(model: str, prompt: str):
  """Query the passed in model for a response."""
  # Build query JSON
  reqBody = {
    "model": model,
    "prompt": prompt,
    "stream": False
  }
  # Query Backend
  response = requests.post(f"{_base()}/api/generate", json=reqBody)
  modelResponse =  response.json()['response']
  return modelResponse


def get_converstaion_response(model: str, conversation: list[dict]):
  """Query the passed in model for a response based on passed in conversation data. Returns raw response from Ollama."""
  # Build query JSON
  reqBody = {
    "model": model,
    "messages": conversation,
    "stream": False
  }
  # Query Backend
  response = requests.post(f"{_base()}/api/chat", json=reqBody)
  resData =  response.json()
  return resData


def delete_model(model_name: str) -> bool:
  """Delete a model from the Ollama server. Returns True on success."""
  try:
    response = requests.delete(f"{_base()}/api/delete", json={"name": model_name}, timeout=30)
    return response.status_code == 200
  except Exception:
    return False


def _to_ollama_message(msg: dict) -> dict:
  """Strip any non-standard fields before sending to Ollama."""
  out = {"role": msg["role"], "content": msg.get("content", "")}
  if "images" in msg:
    out["images"] = msg["images"]
  return out


def stream_conversation_response(model: str, conversation: list[dict], system_prompt: str = ""):
  """Query the passed in model for a streaming response. Yields parsed response chunks until done."""
  llm_messages = [_to_ollama_message(m) for m in conversation if m.get("role") not in ("error",)]
  messages = ([{"role": "system", "content": system_prompt}] + llm_messages) if system_prompt else llm_messages
  reqBody = {
    "model": model,
    "messages": messages,
    "stream": True
  }
  response = requests.post(f"{_base()}/api/chat", json=reqBody, stream=True)
  response.raise_for_status()
  for line in response.iter_lines():
    if line:
      yield json.loads(line)