from textual import work
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Rule, TextArea, Input, DataTable
from textual.containers import Vertical, Horizontal

from utils.ollama_utils import ping_server


class SettingsModal(ModalScreen):

  def __init__(self, servers: list[dict], active_server_name: str):
    super().__init__()
    self._servers: list[dict] = [dict(s) for s in servers]
    self._active_name: str = active_server_name
    self._selected_name: str | None = None
    self._server_statuses: dict[str, str] = {}

  def compose(self) -> ComposeResult:
    with Vertical(id="settingsDialog"):
      yield Label("Settings", id="settingsTitle")
      yield Rule()
      yield Label("Servers", classes="sectionHeader")
      yield DataTable(id="serversTable", cursor_type="row", show_cursor=True)
      with Horizontal(id="serverActions"):
        yield Button("Set Active", id="button_setActiveServer", disabled=True)
        yield Button("Edit", id="button_editServer", disabled=True)
        yield Button("Delete", id="button_deleteServer", variant="error", disabled=True)
      with Vertical(id="editServerRow"):
        with Horizontal(id="editServerInputs"):
          yield Input(placeholder="Name", id="editServerNameInput")
          yield Input(placeholder="http://...", id="editServerUrlInput")
        with Horizontal(id="editServerButtons"):
          yield Button("Confirm", id="button_confirmEditServer", variant="primary")
          yield Button("Cancel", id="button_cancelEditServer")
      yield Label("Add Server", classes="sectionHeader")
      with Horizontal(id="addServerRow"):
        yield Input(placeholder="Name", id="newServerName")
        yield Input(placeholder="http://...", id="newServerUrl")
      yield Button("Test & Add", id="button_testAndAdd")
      yield Label("", id="addServerStatus")
      yield Rule()
      yield Label("System Prompt", classes="sectionHeader")
      yield Label("Sent to the model at the start of every conversation.", classes="settingsHint")
      yield TextArea(self._active_server_prompt(), id="systemPromptInput")
      with Horizontal(id="settingsButtons"):
        yield Button("Save", id="button_saveSettings", variant="success")
        yield Button("Cancel", id="button_cancelSettings")

  def _active_server_prompt(self) -> str:
    server = next((s for s in self._servers if s["name"] == self._active_name), None)
    return server.get("system_prompt", "") if server else ""

  def _save_prompt_to_active_server(self) -> None:
    prompt = self.query_one("#systemPromptInput", TextArea).text
    for s in self._servers:
      if s["name"] == self._active_name:
        s["system_prompt"] = prompt
        break

  def on_mount(self) -> None:
    edit_row = self.query_one("#editServerRow")
    edit_row.display = False
    edit_row.border_title = "Server Edit"
    table = self.query_one("#serversTable", DataTable)
    table.add_column("Active", key="active")
    table.add_column("Name", key="name")
    table.add_column("URL", key="url")
    table.add_column("Ping", key="status")
    self._rebuild_table()
    self._check_all_server_statuses()

  def _rebuild_table(self) -> None:
    table = self.query_one("#serversTable", DataTable)
    table.clear()
    selected_row_idx = None
    for i, server in enumerate(self._servers):
      active_mark = "●" if server["name"] == self._active_name else ""
      status = self._server_statuses.get(server["name"], "Checking...")
      table.add_row(active_mark, server["name"], server["url"], status, key=server["name"])
      if server["name"] == self._selected_name:
        selected_row_idx = i
    if selected_row_idx is not None:
      table.move_cursor(row=selected_row_idx)
    self._update_action_buttons()

  def _check_all_server_statuses(self) -> None:
    for server in self._servers:
      self._check_single_server_status(server["name"], server["url"])

  @work(thread=True)
  def _check_single_server_status(self, name: str, url: str) -> None:
    ms = ping_server(url)
    status_text = f"✓ {ms}ms" if ms is not None else "✗ Offline"
    self.app.call_from_thread(self._update_server_status_cell, name, status_text)

  def _update_server_status_cell(self, name: str, status_text: str) -> None:
    self._server_statuses[name] = status_text
    try:
      table = self.query_one("#serversTable", DataTable)
      table.update_cell(row_key=name, column_key="status", value=status_text)
    except Exception:
      pass  # row deleted before check completed
    if name == self._selected_name:
      self._update_action_buttons()

  def _update_action_buttons(self) -> None:
    no_selection = self._selected_name is None
    status = self._server_statuses.get(self._selected_name, "") if self._selected_name else ""
    online = status.startswith("✓")
    self.query_one("#button_setActiveServer", Button).disabled = no_selection or not online
    self.query_one("#button_editServer", Button).disabled = no_selection
    self.query_one("#button_deleteServer", Button).disabled = len(self._servers) <= 1 or no_selection

  def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
    self._selected_name = event.row_key.value if event.row_key else None
    self._update_action_buttons()

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "button_setActiveServer":
      self._handle_set_active()
    elif event.button.id == "button_editServer":
      self._handle_edit_server()
    elif event.button.id == "button_confirmEditServer":
      self._handle_edit_confirm()
    elif event.button.id == "button_cancelEditServer":
      self.query_one("#editServerRow").display = False
    elif event.button.id == "button_deleteServer":
      self._handle_delete()
    elif event.button.id == "button_testAndAdd":
      self._handle_test_and_add()
    elif event.button.id == "button_saveSettings":
      self._save_prompt_to_active_server()
      self.dismiss({
        "servers": self._servers,
        "active_server_name": self._active_name,
      })
    elif event.button.id == "button_cancelSettings":
      self.dismiss(None)

  def _handle_set_active(self) -> None:
    if self._selected_name is None:
      return
    self._save_prompt_to_active_server()
    self._active_name = self._selected_name
    self.query_one("#systemPromptInput", TextArea).load_text(self._active_server_prompt())
    self._rebuild_table()

  def _handle_edit_server(self) -> None:
    if self._selected_name is None:
      return
    server = next((s for s in self._servers if s["name"] == self._selected_name), None)
    if server is None:
      return
    name_inp = self.query_one("#editServerNameInput", Input)
    url_inp = self.query_one("#editServerUrlInput", Input)
    name_inp.value = self._selected_name
    url_inp.value = server["url"]
    self.query_one("#editServerRow").display = True
    name_inp.focus()

  def _handle_edit_confirm(self) -> None:
    new_name = self.query_one("#editServerNameInput", Input).value.strip()
    new_url = self.query_one("#editServerUrlInput", Input).value.strip().rstrip("/")
    if not new_name:
      self.notify("Name cannot be empty.", severity="error")
      return
    if not new_url:
      self.notify("URL cannot be empty.", severity="error")
      return
    old_name = self._selected_name
    name_changed = new_name != old_name
    if name_changed and any(s["name"] == new_name for s in self._servers):
      self.notify(f'A server named "{new_name}" already exists.', severity="error")
      return
    for s in self._servers:
      if s["name"] == old_name:
        s["name"] = new_name
        s["url"] = new_url
        break
    if self._active_name == old_name:
      self._active_name = new_name
    if name_changed and old_name in self._server_statuses:
      self._server_statuses[new_name] = self._server_statuses.pop(old_name)
    self._selected_name = new_name
    self._server_statuses[new_name] = "Checking..."
    self.query_one("#editServerRow").display = False
    self._rebuild_table()
    self._check_single_server_status(new_name, new_url)

  def _handle_delete(self) -> None:
    if self._selected_name is None or len(self._servers) <= 1:
      return
    self._servers = [s for s in self._servers if s["name"] != self._selected_name]
    if self._active_name == self._selected_name:
      self._active_name = self._servers[0]["name"]
    self._selected_name = None
    self.query_one("#editServerRow").display = False
    self._rebuild_table()

  def _handle_test_and_add(self) -> None:
    name = self.query_one("#newServerName", Input).value.strip()
    url = self.query_one("#newServerUrl", Input).value.strip()
    status = self.query_one("#addServerStatus", Label)

    if not name:
      status.remove_class("success")
      status.add_class("error")
      status.update("Name cannot be empty.")
      return
    if any(s["name"] == name for s in self._servers):
      status.remove_class("success")
      status.add_class("error")
      status.update(f'A server named "{name}" already exists.')
      return
    if not url:
      status.remove_class("success")
      status.add_class("error")
      status.update("URL cannot be empty.")
      return

    self.query_one("#button_testAndAdd", Button).disabled = True
    status.remove_class("success", "error")
    status.update("Testing connection...")
    self._test_and_add(name, url)

  @work(thread=True)
  def _test_and_add(self, name: str, url: str) -> None:
    ms = ping_server(url)
    if ms is not None:
      self.app.call_from_thread(self._on_add_success, name, url)
    else:
      self.app.call_from_thread(self._on_add_failure, f"Could not connect to {url}")

  def _on_add_success(self, name: str, url: str) -> None:
    self._servers.append({"name": name, "url": url, "system_prompt": ""})
    self._rebuild_table()
    self.query_one("#newServerName", Input).value = ""
    self.query_one("#newServerUrl", Input).value = ""
    status = self.query_one("#addServerStatus", Label)
    status.remove_class("error")
    status.add_class("success")
    status.update(f'✓ "{name}" added.')
    self.query_one("#button_testAndAdd", Button).disabled = False

  def _on_add_failure(self, error: str) -> None:
    status = self.query_one("#addServerStatus", Label)
    status.remove_class("success")
    status.add_class("error")
    status.update(error)
    self.query_one("#button_testAndAdd", Button).disabled = False
