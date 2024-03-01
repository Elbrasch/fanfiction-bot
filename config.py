from confz import BaseConfig, FileSource
from typing import Optional

class Config(BaseConfig):
    model_path_mixtral: str
    model_path_noromaid1: str
    model_path_noromaid4: str
    template_prompt_mixtral:str
    template_prompt_noromaid1:str
    selected_model:str
    story: str
    rebuild: bool
    non_story_temperature: float
    CONFIG_SOURCES = FileSource(file="config.yaml")
