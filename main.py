
import logging
from llm import question, chat, set_system_context
import json
from config import Config
import os
import yaml
from story import Story

def json_cleanup(raw: str) -> str:
    print(raw)
    if raw.find("{") == -1:
        raw = "{" + raw
    if raw.find("}") == -1:
        raw = raw + "}"
    return raw[:raw.rfind("}") +1].replace("\\", "")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    with open(Config().story, "r") as f:
        story_config = yaml.load(f, Loader=yaml.FullLoader)
    try:
        if Config().rebuild:
            os.remove(f"{story_config['name']}.json")
            os.remove(f"question.json")
    except:
        pass
    story = Story.load(config=story_config)
    set_system_context(story.system)
    if story.world is None:
        logging.info("generating world")
        story.world = chat(f"The story features the main characters ({story.main_character}). The main plot will be {story.main_plot}.\nThe subplot is {story.sub_plot}\n" +
                            f"Describe the world (Geography, History, Political System, Magic system) the story is set in a few words.")
        story.world = question(story.world, [])
        story.save()
    if story.appearance is None:
        logging.info("generating appearance")
        story.appearance =chat(f"Come up with a short description and appearance of the main character(s).")
        story.appearance =question(story.appearance, [story.world])
        story.save()
    if story.characters is None:
        logging.info("generating characters")
        story.characters = chat(f"List up to 5 other characters that appear in the story. Main Attributes are name, age, look, role in the story, relationship to the main character(s) and personality. Keep the description short. Generate names for all characters!")
        story.characters = question(story.characters, [story.world, story.appearance])
        story.save()
    if story.outline is None:
        logging.info("generating outline")
        story.outline = chat(f"I need a chapter breakdown for the story. Include theme, purpose of the chapter and a detailed chapter summary. Return as a json list.")
        story.outline = question(story.outline, [story.world,  story.appearance, story.characters], as_json=True)
        chapters = json.loads(story.outline.response)
        while True:
            cont = chat("Is the chapter list finished? Answer with only Yes or No.")
            cont = question(cont, [story.world, story.appearance, story.characters, story.outline])
            if cont.response[:3].lower() == "yes":
                break
            raw = chat("Continue")
            raw = question(raw, [story.world, story.appearance, story.characters, story.outline], as_json=True)
            for c in json.loads(raw.response):
                chapters.append(c)
            story.outline.response = json.dumps(chapters)
        story.save()
    logging.info("generating story")
    chapters = json.loads(story.outline.response)
    previous_notes = ""
    story_file = f"{story.name}.txt"
    if os.path.exists(story_file):
        os.remove(story_file)    
    if len(story.scenes) == 0:
        last_scenes = ""
        for i, chapter in enumerate(chapters):
            set_system_context(f"You are a professional author that creates immersive and detailed stories. You are currently working on a story in the setting {story.setting}. The genre of the story is {story.genre}. You use the metric system. You like to show instead of tell in your stories.")
            subchapter_question = f"Give me additional subchapters, covering the content of the chapter {chapter}. List a title, theme, detailed description, viewpoint character and characters. Stop before describing content of the followup chapter."
            scenes_data = f"The world description is:\n{story.world.response}\nPossible main Characters are (through you can add additional characters)\n{story.appearance.response}\n{story.characters.response}"
            raw = chat(subchapter_question)
            raw = question(raw, [chat("Generate a world and character description.", scenes_data), story.outline, chat("What were the subchapters of the last chapter?", last_scenes)], as_json=True)
            last_scenes = raw.response
            story.scenes.extend(json.loads(raw.response))
            story.save()
    last_text = ""
    set_system_context(f"You are a professional author that creates high quality novels. You are currently working on a story in the setting {story.setting} and genre {story.genre} story. You like to show instead of tell in your stories. The world is {story.world.response}.")
    for i, scene in enumerate(story.scenes):
        if i < story.done_scenes:
            continue
        characters = chat(f"What are the characters for this story?", f"Characters are {story.appearance.response}\n{story.characters.response}.\n")
        scene_question = chat(f"Now write a chapter from the following outline in a detailed scene:\n{scene}\nDescribe the scene in detail.\nStop before reaching content of the next scene {story.scenes[min(i+1, len(story.scenes)-1)]}. Write in full sentences and use proper grammar.")
        scene_question = question(scene_question, [characters, chat("Write a subchapter breakdown of the chapters", str(story.scenes[max(0, i-3):i+3])), chat("What was the last subchapter?", last_text)], temperature=0.8)
        scene_text = scene_question.response
        with open(story_file, "a") as f:
            f.write(scene_text + "\n----------------------------\n")
        last_text = scene_text
        story.done_scenes += 1
        story.save()
