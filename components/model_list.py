from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label
from textual.message import Message

from utils.ollama_utils import get_installed_models


class ModelList(Widget):
  """Display a greeting."""

  def __init__(self, ctxObj, id=None):
    super().__init__(id=id)
    self.config = ctxObj['config']
    self.modelNameList = []

  
  def compose(self):
    yield Label("Installed Models:")
    yield ListView(id="modelList")
    

  def on_mount(self):
    # Populate Model List
    self.modelNameList = get_installed_models()
    self.modelList: ListView = self.query_one("#modelList")
    self.build_model_items(self.modelList)
    self.modelList.index = 0
    self.post_message(self.ModelSelected(self.modelNameList[0]))
  

  def build_model_items(self, modelList: ListView):
    for model in self.modelNameList:
      modelList.append(ListItem(Label(model['name'])))


  def on_list_view_selected(self, event: ListView.Selected):
    if(event.list_view.id == "modelList"):
      model_obj = self.modelNameList[event.index]
      self.post_message(self.ModelSelected(model_obj))

  
  class ModelSelected(Message):
    """Model selected message."""
    def __init__(self, model: dict) -> None:
      self.model = model
      super().__init__()