from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Rule, TextArea, Input
from textual.containers import Vertical, Horizontal


class SettingsModal(ModalScreen):

  def __init__(self, current_system_prompt: str, current_url: str):
    super().__init__()
    self.current_system_prompt = current_system_prompt
    self.current_url = current_url

  def compose(self) -> ComposeResult:
    with Vertical(id="settingsDialog"):
      yield Label("Settings", id="settingsTitle")
      yield Rule()
      yield Label("Ollama URL", classes="sectionHeader")
      yield Input(self.current_url, id="ollamaUrlInput")
      yield Label("System Prompt", classes="sectionHeader")
      yield Label("Sent to the model at the start of every conversation.", classes="settingsHint")
      yield TextArea(self.current_system_prompt, id="systemPromptInput")
      with Horizontal(id="settingsButtons"):
        yield Button("Save", id="button_saveSettings", variant="success")
        yield Button("Cancel", id="button_cancelSettings")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "button_saveSettings":
      url = self.query_one("#ollamaUrlInput", Input).value
      prompt_text = self.query_one("#systemPromptInput", TextArea).text
      self.dismiss({"url": url, "system_prompt": prompt_text})
    elif event.button.id == "button_cancelSettings":
      self.dismiss(None)
