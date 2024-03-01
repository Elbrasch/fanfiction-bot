# fanfiction-bot
Fanfiction bot based on local LLM
Put your ideas into the storyideas folder, select the model and story in config.yaml

# Installation
First install llama-cpp. Then install the packages in requirements.txt.
## llama-cpp
Lama-cpp is used to execute the local LLM. For this, you need a C++ compiler or download precompiled binaries.
See https://github.com/abetlen/llama-cpp-python for instructions.
Alternatively download the desired precompiles here https://github.com/ggerganov/llama.cpp/releases
For Windows, install Visual studio and compile the desired libraries manually beforehand.
I recommend to only compile GPU support (CUBLAS: CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python)
in if you can fit a significant amount of the model into VRAM. Otherwise just install with pip install llama-cpp-python.
For reference, I have a 3080 with 10 GB VRAM and an AMD Ryzen 5600X. I see almost no performance improvement when
outsorcing 5 LLM layers to the GPU with a 40 GB Mixtral Model. It is only relevant to me when using 7B LLama models.

## Download the LLMs
You can use any LLM that is instruct trained as long as you provide it's template and add the appropriate class in llm.py
Download the desired model, safe it to /model/ and update config.yaml
Out of the box the following is supported:
- Mixtral Instruct: https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF
  Mistrals demo chat LLM trained on public Chat-GPT instructions. Very PG-13. Follows instructions reasonably well
- Noramaid 1: https://huggingface.co/NeverSleep/Noromaid-v0.1-mixtral-8x7b-Instruct-v3-GGUF/tree/main
  Select one of the quantizations that fit your machine (or be a baller and run the non-quantized version)
  Trained on Roleplay and explicitly filtered content from OpenAI. Somewhat worse at following instructions than Mixtral Instruct,
  but this is completely migrated by the use of json Grammar.
- Noromaid 4: https://huggingface.co/TheBloke/Noromaid-v0.4-Mixtral-Instruct-8x7b-Zloss-GGUF
  Same quanitization versions as Noromaid 1. Consult this ones readme for the different traidoffs between size and quality.
  New version of Noromaid 1. Even less likely to refuse any spicy story idea than the other two models. Slightly worse in 
  writing quality, somewhat sensitive to temperature, context length and previous history writing style.

# Execution
python main.py