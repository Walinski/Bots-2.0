#!/bin/bash

MODEL_TYPE="${OLLAMA_MODEL_TYPE:-llama3}"

# Start Ollama server in the background
ollama serve &

# Wait until the Ollama server is active
while ! ollama list | grep -q 'NAME'; do
  sleep 1
done

# Create custom models based on personas.json
MODELS="/app/houdini/houdini/plugins/bots/languagemodel/models"

echo "Listing model files in $MODELS:"
ls -l "$MODELS"

# Iterate over each model file in the MODELS directory
for model_file in "$MODELS"/*; do
  model_name=$(basename "$model_file")
  echo "Defining custom model: $model_name from path: $model_file"
  ollama create "$model_name" -f "$model_file"
done

echo "Running $MODEL_TYPE"
ollama run "$MODEL_TYPE"