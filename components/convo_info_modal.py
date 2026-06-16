from datetime import datetime, timezone
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Rule
from textual.containers import Vertical


def _fmt_size(bytes: int) -> str:
  if bytes >= 1_000_000_000:
    return f"{bytes / 1_000_000_000:.1f} GB"
  return f"{bytes / 1_000_000:.0f} MB"


def _fmt_duration(seconds: float) -> str:
  seconds = int(seconds)
  if seconds < 60:
    return f"{seconds} seconds"
  minutes = seconds // 60
  if minutes < 60:
    return f"{minutes} minute{'s' if minutes != 1 else ''}"
  hours = minutes // 60
  mins = minutes % 60
  result = f"{hours} hour{'s' if hours != 1 else ''}"
  if mins:
    result += f" {mins} minute{'s' if mins != 1 else ''}"
  return result


def _parse_ts(ts: str) -> datetime | None:
  try:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
  except Exception:
    return None


class ConvoInfoModal(ModalScreen):

  def __init__(self, convo: dict) -> None:
    super().__init__()
    self.convo = convo

  def compose(self) -> ComposeResult:
    convo = self.convo
    model = convo.get('model', {})
    messages = convo.get('messages', [])
    details = model.get('details', {})

    model_parts = [model.get('name', 'Unknown')]
    if details.get('family'):
      model_parts.append(details['family'].capitalize())
    if details.get('parameter_size'):
      model_parts.append(details['parameter_size'])
    if details.get('quantization_level'):
      model_parts.append(details['quantization_level'])
    if model.get('size'):
      model_parts.append(_fmt_size(model['size']))
    model_str = '  ·  '.join(model_parts)

    user_msgs = [m for m in messages if m.get('role') == 'user']
    asst_msgs = [m for m in messages if m.get('role') == 'assistant']
    err_msgs  = [m for m in messages if m.get('role') == 'error']
    attach_count = sum(1 for m in user_msgs if m.get('images'))

    word_count = sum(len(m.get('content', '').split()) for m in user_msgs + asst_msgs)
    char_count = sum(len(m.get('content', ''))          for m in user_msgs + asst_msgs)

    timed_msgs = [m for m in messages if m.get('role') in ('user', 'assistant') and m.get('timestamp')]
    timestamps = [_parse_ts(m['timestamp']) for m in timed_msgs]
    timestamps = [t for t in timestamps if t is not None]

    with Vertical(id="infoDialog"):
      yield Label("Conversation Info", id="infoTitle")
      yield Rule()

      yield Label("Conversation", classes="infoSectionLabel")
      yield Label(f"  Title:   {convo.get('title', '—')}", markup=False)
      yield Label(f"  Model:   {model_str}", markup=False)
      yield Rule()

      yield Label("Messages", classes="infoSectionLabel")
      msg_line = f"  Total: {len(messages)}   User: {len(user_msgs)}   Assistant: {len(asst_msgs)}"
      if err_msgs:
        msg_line += f"   Errors: {len(err_msgs)}"
      if attach_count:
        msg_line += f"   Attachments: {attach_count}"
      yield Label(msg_line, markup=False)
      if messages:
        yield Label(f"  Words: ~{word_count:,}   Characters: ~{char_count:,}", markup=False)

      if len(timestamps) >= 2:
        yield Rule()
        yield Label("Timeline", classes="infoSectionLabel")
        fmt = "%Y-%m-%d %H:%M UTC"
        first = timestamps[0].astimezone(timezone.utc).strftime(fmt)
        last  = timestamps[-1].astimezone(timezone.utc).strftime(fmt)
        duration = _fmt_duration((timestamps[-1] - timestamps[0]).total_seconds())
        yield Label(f"  Started:  {first}", markup=False)
        yield Label(f"  Last:     {last}", markup=False)
        yield Label(f"  Duration: {duration}", markup=False)

      yield Rule()
      yield Button("Close", id="button_closeInfo")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "button_closeInfo":
      self.dismiss()

  def on_key(self, event) -> None:
    if event.key == "escape":
      self.dismiss()
