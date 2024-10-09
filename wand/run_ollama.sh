#!/bin/bash

MODEL_TYPE="${OLLAMA_MODEL_TYPE:-llama3}"

ollama serve &

# Wait until the Ollama server is active
while ! ollama list | grep -q 'NAME'; do
  sleep 1
done

echo "Ollama is active. Pulling $MODEL_TYPE model..."

ollama pull "$MODEL_TYPE"
