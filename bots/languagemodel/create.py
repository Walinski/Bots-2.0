# Standard Imports
import os
import json

# Package Imports
from . import logger

# https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values

class PersonaFileCreator:
    
    personas = {}

    @classmethod
    def load_personas(cls):
        if not cls.personas:
            _personas_path = os.path.join(os.path.dirname(__file__), 'personas.json')
            with open(_personas_path) as f:
                cls.personas = json.load(f)

    @classmethod
    def build_models(cls):
        cls.load_personas()

        models_path = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(models_path, exist_ok=True)

        custom_model = os.path.join(models_path, "base-model")

        with open(custom_model, 'r') as f:
            base_contents = f.read()

        for key, value in cls.personas.items():
            path = os.path.join(models_path, key.replace(" ", "_"))

            if os.path.exists(path):
                logger.info(f"{path} exists. Skipping.")
                continue

            contents = base_contents.replace( # Replace the base model with the persona
                "SYSTEM You are a helpful AI assistant named Llama3 Droid",
                f"SYSTEM {value}"
            )

            with open(path, 'w') as f:
                f.write(contents)
                logger.info(f"File {path} created.")