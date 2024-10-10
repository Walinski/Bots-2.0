import aiohttp
import json, re, os
import logging, asyncio
from typing import Optional
from .badword import is_profane
from venv import logger

# https://www.datacamp.com/tutorial/run-llama-3-locally
# https://ollama.com/download/linux
# https://www.arsturn.com/blog/running-ollama-in-a-docker-environment-your-complete-guide
# https://secretdatascientist.com/ollama-cheatsheet/
# https://github.com/rawanalkurd/Generative-AI-DSPy/blob/main/Running%20LLMs%20Locally%20A%20Guide%20to%20Setting%20Up%20Ollama%20with%20Docker.ipynb

YELLOW_FADED = "\033[2;33m"
RESET = "\033[0m"

class DEBUGRedFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        return f"{YELLOW_FADED}{message}{RESET}"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = DEBUGRedFormatter('%(asctime)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

'''Prerequisites'''
# chmod +x run_ollama.sh
# Run the docker-compose.yml
# Note - Ollama will need to download and install.
# Houdini can still be logged into and joined.

'''Ollama can run with GPU acceleration inside Docker containers for Nvidia GPUs.'''
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation
# chmod +x nvidia_install.sh
# ./nvidia_install.sh

class OLLAMA:
    api_endpoint = "http://ollama:11434/api/generate"
    queue = asyncio.Queue()  # FIFO Queue
    models = {}
    personas = {}

    @classmethod
    def _load_personas(cls):
        if not cls.personas:
            _personas_path = os.path.join(os.path.dirname(__file__), 'personas.json')
            with open(_personas_path) as f:
                cls.personas = json.load(f)

    def __new__(cls, model_name, api_endpoint=None, **kwargs):
        if model_name not in cls.models:
            instance = super().__new__(cls)
            cls.models[model_name] = instance
            instance._initialize(model_name, api_endpoint, **kwargs)
        return cls.models[model_name]

    def _initialize(self, model_name, api_endpoint=None, **kwargs):
        self._load_personas()
        self.model_name = model_name
        self.session = aiohttp.ClientSession()
        self.kwargs = {
            "temperature": 0.7,
            "n": 1,
            "max_tokens": 100,
            "top_p": 0.9,
            "top_k": 50,
            "presence_penalty": 0.6,
            "frequency_penalty": 0.0,
            **kwargs
        }
        logger.info(f"Loaded Parameters with MODEL: {model_name}, API: {self.api_endpoint}, kwargs: {self.kwargs}")

    @classmethod
    async def push(cls, item):
        await cls.queue.put(item)

    @classmethod
    async def debug_queue(cls, context=""):
        queue_size = cls.queue.qsize()
        queue_contents = list(cls.queue._queue) 
        logger.debug(f"({context}) - Size: {queue_size}, Contents: {queue_contents}")

    async def generate(self, message: str = "", **kwargs):
        payload = {'model': self.model_name, 'prompt': message, **self.kwargs, **kwargs}
        complete = ""

        try:
            async with self.session.post(self.api_endpoint, json=payload, timeout=10) as r:
                if r.status == 200:
                    async for token in r.content:
                        if token:
                            j = json.loads(token.decode('utf-8'))
                            complete += j.get("response", "")
                            if j.get("done", True):
                                break
                else:
                    print(f"Error: Received status code {r.status}")

        except aiohttp.ClientConnectorError:
            logger.info(f"{self.model_name} is unavailable.")
        except asyncio.TimeoutError:
            logger.info("Response Time Elapsed")
        except Exception as e:
            logger.error(f"Unexpected Exception: {str(e)}")
        finally:
            return complete

    async def __call__(self, BOT: Optional[object] = None, nickname: str = "", question: str = "", **kwargs):

        await self.push(question)
        await self.debug_queue(f"{nickname} Pending")
        message = self.personas.get(nickname, "") + question
        logger.info(f"{nickname} is thinking")

        complete = await self.generate(message, **kwargs)
        
        await self.queue.get()
        self.queue.task_done()
        await self.debug_queue(f"{nickname} Finished")
        logger.info(f"{nickname} is responding")

        asyncio.create_task(respond(BOT, complete))
        

    async def close(self):
        await self.session.close()

async def send_question(BOT: Optional[object] = None, nickname: str = "", question: str = "") -> None:

    if await is_profane(logger, question):
        logger.error("Message Ignored!")
        return

    await OLLAMA('llama3', temperature=0.7)(BOT, nickname, question)

    if __name__ == "__main__":
        new_question = input("Enter your question: ")
        await send_question(question=new_question, nickname=nickname)

async def respond(BOT: Optional[object] = None, response: str = ""):
    sentences = re.split(r'(?<=[.!?])\s+|\n\n', response)
    for sentence in sentences:
        if BOT:
            await BOT.room.send_xt('sm', BOT.id, sentence)
        else:
            print(sentence)

        await asyncio.sleep(3)

    if BOT:
        BOT.is_ready_to_listen = True

'''Debugging'''
# docker ps
# docker exec -it <houdini container id> /bin/sh
# Run the following command to be compatible with relative imports
# python -m houdini.plugins.bots.languagemodel.converse

if __name__ == "__main__":
    initial_question = input("Enter your question: ")
    nickname = input("Enter nickname: ")
    asyncio.run(send_question(question=initial_question, nickname=nickname))
