from llama_cpp import Llama, LlamaGrammar
import logging
import time
from dataclasses import dataclass
import jsonpickle
from config import Config

def persist_to_file(file_name):

    def decorator(original_func):

        try:
            with open(file_name, 'r') as f:
                cache = jsonpickle.decode(f.read())
        except (IOError, ValueError):
            cache = {}

        def new_func(param1, llm_arguments):
            param = str(param1) + str(llm_arguments)
            if param not in cache:
                cache[param] = original_func(param1, llm_arguments)
                with open(file_name, 'w') as f:
                    f.write(jsonpickle.encode(cache))
            return cache[param]

        return new_func

    return decorator


class Model:
    def __init__(self, template:str) -> None:
        self.template = template
        
    def _prompt(self, question:str, result: str) -> str:
        return self.template.format(prompt=question, result=result)
    
    def history_prompt(self, question:str, result: str) -> str:
        return self._prompt(question=question, result=result)
    
    def question_prompt(self, question:str) -> str:
        return self._prompt(question=question, result="")


class Mixtral(Model):
    def __init__(self) -> None:
        super().__init__(Config().template_prompt_mixtral)
        self.model = Llama(
            model_path=Config().model_path_mixtral,  # Download the model file first
            n_ctx= 32768,
            n_threads=10,            # The number of CPU threads to use, tailor to your system and the resulting performance
            )

    def system_prompt(self, system:str) -> str:
        return self._prompt(question=system, result="Ok, I will act in accordance of this instruction.")
    
    def question_prompt(self, question:str) -> str:
        res = super().question_prompt(question).replace("</s>", "")
        return res
    
    def stream(self, prompt, llm_params):
        return self.model(prompt, # Prompt
            max_tokens=32768,  # Generate up to 512 tokens
            stop=["</s>"],   # Example stop token - not necessarily correct for this specific model! Please check before using.
            echo=True,        # Whether to echo the prompt
            stream=True,
            **llm_params)
    
class Noromaid1(Model):
    def __init__(self) -> None:
        super().__init__(Config().template_prompt_noromaid1)
        self.model = Llama(
            model_path=Config().model_path_noromaid1,  # Download the model file first
            n_ctx= 32768,
            n_threads=10,            # The number of CPU threads to use, tailor to your system and the resulting performance
            )

    def system_prompt(self, system:str) -> str:
        return f"### Instruction:\n{system}\n"
    
    def history_prompt(self, question:str, result: str) -> str:
        return super().history_prompt(question, result) + "\n"

    def stream(self, prompt,llm_params):
        return self.model(prompt, # Prompt
            max_tokens=32768,  # Generate up to 512 tokens
            stop=["### Input:"],   # Example stop token - not necessarily correct for this specific model! Please check before using.
            echo=True,        # Whether to echo the prompt
            stream=True,
            **llm_params
            )

class Noromaid4:
    def __init__(self) -> None:
        self.template = "<|im_start|>{message_type}\n{message}<|im_end|>"
        self.model = Llama(
            model_path=Config().model_path_noromaid4,  # Download the model file first
            n_ctx= 32768,
            n_threads=10,            # The number of CPU threads to use, tailor to your system and the resulting performance
            )
        
    def _prompt(self, message_type:str, message: str) -> str:
        return self.template.format(message_type=message_type, message=message)
    
    def history_prompt(self, question:str, result: str) -> str:
        user = self._prompt("user", question)
        answer = self._prompt("assistant", result)
        return user + "\n" + answer
    
    def question_prompt(self, question:str) -> str:
        return self._prompt("user", question) + "\n<|im_start|>assistant\n"

    def system_prompt(self, system:str) -> str:
        return self._prompt("system", system)

    def stream(self, prompt, llm_params):
        return self.model(prompt, # Prompt
            max_tokens=32768,  # Generate up to 512 tokens
            stop=["<|im_end|>"],  
            echo=True,        # Whether to echo the prompt
            stream=True,
            **llm_params
            )
        
def json_grammar():
    with open("json.gbnf", "r") as  f:
        return LlamaGrammar.from_string(f.read())


def load_model():
    selected = Config().selected_model
    if selected == "mixtral":
        return Mixtral()
    elif selected == "noromaid1":
        return Noromaid1()
    elif selected == "noromaid4":
        return Noromaid4()
    raise NotImplementedError(f"don't know {selected}")


llm = load_model()
system_context = "You are an helpful AI assistant."


def set_system_context(context):
    global system_context
    system_context = context

def token_amount(text:str)-> int:
    return len(llm.model.tokenize(text.encode("utf-8")))

@dataclass
class chat:
    prompt: str
    response: str = ""

@persist_to_file("question.json")
def _question(prompt: str, llm_arguments)->str:
    output = llm.stream(prompt, llm_params=llm_arguments)
    result = ""
    handler = logging.StreamHandler()
    for o in output:
        handler.stream.write(o["choices"][0]["text"])
        handler.flush()
        result += o["choices"][0]["text"]
        if "usage" in o:
            logging.debug(o["usage"])
    return result

def question(question:chat, context:list[chat], as_json:bool = False, temperature=None, repeat_penalty=1.1)-> chat:
    if temperature is None:
        temperature = Config().non_story_temperature
    prompt = llm.system_prompt(system_context) + "\n"
    for c in context:
        prompt += llm.history_prompt(c.prompt, c.response) + "\n"
    prompt += llm.question_prompt(question.prompt)
    params = {"repeat_penalty": repeat_penalty, "temperature": temperature}
    logging.info(prompt)
    num_prompt_tokens = token_amount(prompt)
    logging.info(f"prompt token length {num_prompt_tokens}")
    grammar = None
    if as_json:
        params["grammar"] = json_grammar()
    start = time.time()
    result = _question(prompt, llm_arguments=params)
    end = time.time()
    num_result_tokens = token_amount(result)
    logging.debug(f"Time taken for interference: {end - start}")
    logging.debug(f"result token length {num_result_tokens}, overall token length {num_prompt_tokens + num_result_tokens}, seconds per generated token {((end - start) / (num_result_tokens))} s")
    question.response = result
    return question

