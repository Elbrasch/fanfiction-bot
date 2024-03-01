import jsonpickle
import os
from typing import Optional
from llm import chat


class Story:
    name: str
    setting:str
    genre: str
    main_character :str
    main_plot:str
    sub_plot:str
    system:str
    scenes: tuple 
    done_scenes: int 
    outline: Optional[chat] 
    world: Optional[chat]
    appearance: Optional[chat] 
    characters: Optional[chat] 
    def __init__ (self, config:dict):
        self.name = config["name"]
        self.setting = config["setting"]
        self.genre = config["genre"]
        self.main_character = config["main_character"]
        self.main_plot = config["main_plot"]
        self.sub_plot = config["sub_plot"]
        self.system = f"You are an expert world builder helping authors to create their own worlds that cater to mature audiences. You are currently working on a story in the setting {self.setting}. The genre of the story is {self.genre}. You use the metric system."
        if "additional_info" in config:
            self.system +=  config["additional_info"]
        self.scenes = []
        self.done_scenes = 0
        self.outline = None
        self.world = None
        self.appearance = None
        self.characters = None

    def save(self):
        path = self.name
        print(f"saving to {path}.json: {self.scenes}")
        print(jsonpickle.encode(self, indent=4))
        with open(f"{path}.json", "w") as f:
            f.write(jsonpickle.encode(self, indent=4, max_depth=-1))

    @classmethod
    def load(cls, config) -> "Story":
        path = config["name"] + ".json"
        print(f"loading from {path}")
        if not os.path.exists(path):
            return cls(config)
        with open(path, "r") as f:
            return jsonpickle.decode(f.read())
