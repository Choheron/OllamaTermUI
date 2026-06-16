# OllamaTermUI

Textual TUI for chatting with Ollama. Python 3.10+.

## Running

```bash
pip install -r requirements.txt
python ollamatermui.py
```

## Project structure

```
ollamatermui.py           # App class, all modals, event handlers, global state
components/               # Textual widgets and modal screens
tcss/                     # Per-component TCSS stylesheets
utils/
  ollama_utils.py         # Ollama HTTP API calls
  conversational_utils.py # Conversation read/write to disk
  config.py               # Server config read/write to disk
```

Data is stored in `~/.ollamatermui/`:
- `config.json` — servers list and active server
- `conversations/[server_name]/[id].json` — one file per conversation

## Architecture

`OllamaTermUI(App)` owns all state (`self.conversations`, `self.active_convo_id`, `self.installed_models`, `self.servers`). The sidebar is a permanent `Vertical#sidebar`; the chat area is a `Vertical#chatContainer` that mounts/unmounts a fresh `ChatBox` widget each time the active conversation changes.

Modals extend `ModalScreen` and are pushed with `self.push_screen(Modal(...), callback)`. The callback receives the value passed to `modal.dismiss(value)`.

Long-running work (API calls, model loading) uses `@work(thread=True)`. To update UI from a worker thread, always use `self.app.call_from_thread(fn, *args)` — direct widget mutation from a thread will crash.

### Child → parent communication

`ChatBox` defines `Message` subclasses for events it emits:
- `RenameConversationRequested`
- `DeleteConversationRequested`
- `UpdateConversationTitle`
- `ConversationSaveRequested`

The app handles them via `on_chat_box_<message_name_snake>()` methods — Textual routes these automatically by naming convention.

## Adding a new modal

1. Create `components/my_modal.py` extending `ModalScreen`
2. Create `tcss/my_modal.tcss` with `MyModal { align: center middle; }` and `#myDialog { ... }`
3. Import in `ollamatermui.py`
4. Add `"tcss/my_modal.tcss"` to `CSS_PATH` in `OllamaTermUI`
5. Call `self.push_screen(MyModal(...), callback)` from a handler

## Adding a sidebar button

1. `yield Button("Label", id="button_myAction", disabled=True)` in `compose()` after the existing buttons
2. Add `#button_myAction { width: 100%; }` to `tcss/ollamaui.tcss`
3. Handle it in `on_button_pressed` with `elif event.button.id == "button_myAction"`
4. Enable/disable it in `_update_summarize_button()` (or a new dedicated method called from the same places)

## Textual gotchas

- **Widget IDs must be unique** across the entire widget tree. If a widget is composed multiple times (e.g., section headers in a loop), use `classes="myClass"` and style with `.myClass` — never reuse an `id`.
- **TCSS files must be registered** in `CSS_PATH` or their styles are ignored silently.
- **`call_from_thread` is required** when updating widgets from a `@work(thread=True)` worker. Skipping it causes silent failures or crashes.
- **`@work(exclusive=True)`** ensures only one instance of a worker runs at a time — used for streaming responses to prevent overlapping replies.

## CSS conventions

Border colors by intent:
- `$error` — destructive actions (delete dialogs)
- `$warning` — edits/changes (rename dialog)
- `$accent` — informational (summary, info modals)
- `$primary` — neutral

Modal dialog containers: `width: 40–70`, `padding: 1 2`, `background: $surface`, `height: auto`.
