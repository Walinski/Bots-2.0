# Standard Imports
import random
import asyncio
import time
import datetime
import json
import re
import os
import math
from typing import Optional

# External Imports
import pytz
import aiohttp

# Package Imports
from . import *
from .badword import contains_badword
from .create import PersonaFileCreator
from .splitter import retrieve_sentences

################################################################

class Ollama:
    """Class for handling Ollama model interactions"""
    
    queue = asyncio.Queue()  # Asynchronous FIFO Queue
    session = None

    @classmethod
    def initialize_session(cls):
        """Initializes the aiohttp session if not already initialized"""
        if cls.session is None:
            cls.session = aiohttp.ClientSession()

    @classmethod
    async def close_session(cls):
        """Closes the aiohttp session"""
        if cls.session is not None:
            await cls.session.close()
            cls.session = None

    def __init__(self, model_name, **kwargs):
        self.custom_model = model_name.replace(" ", "_")
        self.api_url = "http://ollama:11434/api/generate"
        self.initialize_session()
        self.kwargs = kwargs  # Custom Parameters
        logger.info(f"Initialized model: {self.custom_model}, API: {self.api_url}, kwargs: {self.kwargs}")

    @classmethod
    async def push(cls, item):
        """Pushes an item into the async queue"""
        await cls.queue.put(item)

    @classmethod
    async def debug_queue(cls, model_name):
        """Logs the current state of the queue"""
        queue_size = cls.queue.qsize()
        contents = list(cls.queue._queue)
        logger.debug(f"({model_name}) - Queue size: {queue_size}, Contents: {contents}")

    async def generate(self, message: str = "", **kwargs):
        """Generates a response using the Ollama model"""
        payload = {'model': self.custom_model, 'prompt': message, **self.kwargs, **kwargs}
        logger.info(f"payload: {payload}")
        complete_response = ""
        
        try:
            async with self.session.post(self.api_url, json=payload, timeout=10) as response:
                if response.status == 200:
                    async for token in response.content:
                        if token:
                            j = json.loads(token.decode('utf-8'))
                            complete_response += j.get("response", "")
                            if j.get("done", True):
                                break
                else:
                    logger.error(f"Error: Received status code {response.status}")
        except aiohttp.ClientConnectorError:
            logger.error(f"{self.custom_model} is unavailable.")
        except asyncio.TimeoutError:
            logger.error("Request timed out.")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")

        return complete_response

    async def recursive_call(self, sentences: str = "", respondees: list = [], response_obj: Optional[object] = None, recursion_depth: int = 0, debug: bool = False):
        """Handles selecting a new respondee and calling recursively"""

        if debug:  
            other_respondents = [name for name in respondees if name != self.custom_model]
            self.custom_model = random.choice(other_respondents)

        else:  
            other_respondents = [b for b in respondees if b != response_obj and b.called]

            if not other_respondents:
                logger.info("No respondents.")
                return

            nickname, response_obj = await retrieve_respondee(response_obj, other_respondents, sentences)

            if not response_obj:
                logger.info("No respondee.")
                return

            self.custom_model = nickname.replace(" ", "_")

        max_recursion = random.randint(2, 4)
        logger.info(f"Recursion : {recursion_depth} / {max_recursion}")

        if recursion_depth <= max_recursion:
            await self.__call__(sentences, respondees, response_obj, recursion_depth + 1)

    async def __call__(self, message: str = "", respondees: list = [], response_obj: Optional[object] = None, recursion_depth: int = 0, max_recursion: int = 3, debug: bool = False, **kwargs):

        if recursion_depth > max_recursion:
            logger.info(f"Max recursion depth reached: {max_recursion}")
            return

        await self.push(message)
        await self.debug_queue(f"{self.custom_model} started processing")

        sentences = await self.generate(message, **kwargs)

        await self.queue.get()
        self.queue.task_done()
        await self.debug_queue(f"{self.custom_model} finished processing")

        logger.info(f"{self.custom_model} generated response")

        task = asyncio.create_task(respond(self, respondees, self.custom_model, response_obj, sentences, recursion_depth, debug=debug))
        if debug:
            await task

####################################################################################################
# Helper Functions

emoticon_keywords = {}

async def handle_emoticon(b, response: str):
    """Retrieves and sends the appropriate emoticon for the given response"""

    async def send_emote(b, emote: int):
        logger.info(f"Sending emote: {emote}")
        await b.room.send_xt('se', b.id, emote)

    def load_emoticons(file_name: str):
        """Loads emoticon data from a file"""
        with open(os.path.join(os.path.dirname(__file__), file_name)) as f:
            return json.load(f)

    if not emoticon_keywords:
        for emotion, data in load_emoticons('emotions.json').items():
            for keyword in data["keywords"]:
                emoticon_keywords[keyword] = (emotion, data["emoticon_id"])

    for word in response.lower().split():
        if word in emoticon_keywords:
            emotion, emoticon = emoticon_keywords[word]
            logger.info(f"Detected emotion: {emotion}, Emoticon: {emoticon} with word {word}")

            if b: await send_emote(b, emoticon)

async def retrieve_respondee(queryer_obj, participants, message, debug: bool = False):
    
        distance = math.inf
        response_obj = None

        if debug == False:
            for b in participants:

                if b.room.id != queryer_obj.room.id: # has been moved!
                    continue

                if any(subname in message.lower() for subname in queryer_obj.username.lower().split()):
                    response_obj = b
                    break  # Exit early if a username match is found

                if queryer_obj:
                    new_distance = math.dist((b.x, b.y), (queryer_obj.x, queryer_obj.y))
                    if new_distance < distance:
                        distance = new_distance
                        response_obj = b

            if response_obj:
                nickname = response_obj.nickname
  
        if debug == True:
            nickname = random.choice(participants)

        return nickname, response_obj

async def PST(TimeZone: str = 'America/Vancouver') -> str:
    """Returns the time in Penguin Standard Time"""
    return datetime.datetime.now(pytz.timezone(TimeZone)).strftime('%I:%M%p').lower()

async def send_PST(response_obj, participants, debug):
        T = f"It's currently {await PST()}"
        logger.info(T)
        if debug == False:
            await response_obj.room.send_xt('sm', response_obj.id, T)
            for b in participants: 
                b.talking = False

async def do_sample(participants: list):
    """Randomly samples participants and marks them as talking"""
    if len(participants) >= 1:
        if len(participants) >= 3:
            selected = random.sample(participants, random.randint(3, len(participants)))  # Randomly sample
        else:
            selected = participants
        for p in participants:
            p.talking = p in selected  # Mark the selected ones as talking
        return selected

####################################################################################################

async def new_conversation(message: str = "", participants: list = [], p: Optional[object] = None, debug: bool = False):
    """Handles a new conversation message, checking for bad words and responding appropriately"""
    if await contains_badword(message):
        return logger.error("Message is inappropriate")
   
    nickname, response_obj = await retrieve_respondee(p, participants, message, debug)

    if any(query in message.lower() for query in {"what's the time", "tell me the time"}): # handle Penguin Time queries
        return await send_PST(response_obj, participants, debug)

    await Ollama(model_name=nickname)(message, participants, response_obj, debug=debug)

####################################################################################################

async def respond(ollama, respondees, nickname, response_obj, raw_response, recursion_depth, debug: bool = False):

    sentences = await retrieve_sentences(raw_response)

    async def check_for_wave(sentence):
        words = sentence.split()
        greetings = {"ahoy", "hey", "hello", "greetings", "hi", "howdy", "hiya", "yo"}
        for word in words:
            if word in greetings:
                logger.info(f"wave is valid: '{word}'")
                response_obj.frame = 25
                return await response_obj.room.send_xt('sf', response_obj.id, response_obj.frame)
 
    async def send_response(sentence):
        logger.info(f"{nickname}: {sentence}")
        if response_obj:
            await response_obj.room.send_xt('sm', response_obj.id, sentence) # send message to room
            await check_for_wave(sentence)
        await asyncio.sleep(min(1.0 + len(sentence) * 0.05, 5.0))

    if debug:
        LoggerFormatting.set_color(BRIGHT_BLUE)

    for sentence in sentences:
        await send_response(sentence)

    if debug:
        LoggerFormatting.set_color(GREY_FADED)

    await handle_emoticon(response_obj, raw_response)

    if response_obj:
        response_obj.talking = False

    await ollama.recursive_call(raw_response, respondees, response_obj, recursion_depth, debug=debug)

#################################################################################################### DEBUG

# docker ps
# docker exec -it <houdini container id> /bin/sh
# python -m houdini.plugins.bots.languagemodel.converse

if __name__ == "__main__":
    PersonaFileCreator.build_models()
    message = input("Enter your question: ")
    nickname = input("Enter nickname: ")
    participants = [nickname, "Cadence", "Gary"]
    asyncio.run(new_conversation(message, participants, debug=True))

