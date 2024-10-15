# Bots 2.0 for Houdini

A continuation of **https://github.com/brosquinha/houdini-bot-plugin**

## This is still in Beta!

![GIF](https://github.com/Walinski/Bots-2.0/blob/main/Rockhopper.gif?raw=true)
![GIF](https://github.com/Walinski/Bots-2.0/blob/main/MigratorGreeting.gif?raw=true)
## Features

1. **Spawning (Mascots/) Bots**
   - Command: `!spawn <nickname>`
   - Description: Spawns a bot with the specified nickname or summon existing bots to your location.
    
2. **Change Bots' Population**
   - Command: `!bpop <integer>`
   - Description: Adjusts the number of bots (0 - 100) in the game. If a lower population is specified, bots will leave the game.

3. **Purge and Remove All Bots**
   - Command: `!bpurge`
   - Description: Removes all bots from the game.

4. **Removing Specific Bots**
   - Command: `!brmv <nickname>`
   - Description: Removes a specific bot by nickname.
   - Mascots' accounts are preserved as no longer bots.

5. **Restyling Bots**
   - Command: `!restyle <username>`
   - Description: Changes bots' equipped clothing items to match the player's equipped items.

6. **Entering Igloos**
   - Description: All bots are generated with random igloos and locations which are open.

7. **Simulating Fluid Movements**
   - Description: Bots move to random positions within pre-specified boundaries using trigonometry.

8. **Simulating Bots Joining and Leaving**
   - Description: Bots can join and leave the game, simulating player rotation.

9. **Following Players**
   - Command: Quickchat "Follow Me"
   - Description: Bots near the player will follow them, tracking coordinates with an offset.

10. **Reactions**
    - Bots react when snowballs are thrown at them and when greeted with quickchat messages.

12. **Playing Sled Racing**
    - Description: Bots can join the Sled Racing minigame if you wait in the queue at the ski hill.

13. **Performing Special Actions**
    - Description: Bots perform special actions at specific spots in certain rooms (e.g., playing drums at the lighthouse, using a pizza apron at the pizza parlor).

14. **Procedurally Generated Names**
    - Description: Bots' names are generated using a Python library for fantasy names, ensuring no two bots have the same name.
   
15. **Talking to Bots**
    - Mascots have prewritten personalities and can be spawned in as bots
    - Ollama AI and Llama3, running offline on a localhost server in a Docker container.
    - Responses are queued with Python asyncio.

## Installation P1

1. Clone the repository
2. Replace requirements.txt in houdini/
4. Run "docker-compose build" in wand/ to install the requirements for Python

## Installation P2

5. Add the contents of bots/wand to wand/
6. chmod +x run_ollama.sh
7. Configure the docker-compose.yml settings for ollama:

# Ollama Configuration

This section describes the configuration for the Ollama service in our Docker Compose setup.

### Build Configuration
- **Context**: The build context is set to the current directory (`.`).
- **Dockerfile**: Uses a custom Dockerfile named `Dockerfile.ollama`.

### Container Settings
- **Container Name**: The container is named `ollama`.
- **Environment File**: Uses `.env` in `/wand`.
- **Entrypoint**: Runs a custom script `/tmp/run_ollama.sh` on startup.

### Networking
- **Port Mapping**: Exposes port 11434 for ollama API, mapping it to the same port on the host. 
- **Network**: Connected to the same network named `wand`.

### Volumes
- Mounts the directory to `/app/` in the container.
- Mounts `./ollama/ollama` to `/root/.ollama` for persistent data storage.

### Environment Variables
- `OLLAMA_KEEP_ALIVE`: Sets connection keep-alive duration to 10 minutes.
- `OLLAMA_LOAD_TIMEOUT`: Sets model loading timeout to 10 minutes.
- `OLLAMA_FLASH_ATTENTION`: Flash Attention uses a more memory-efficient algorithm that reduces the memory requirements for attention computation.
- `OLLAMA_NOHISTORY`: Disables the remembering of interaction history if true.
- `OLLAMA_NUM_PARALLEL`: Sets the number of parallel processing requests. Default 1.
- `OLLAMA_NUM_THREADS`: Limits the number of threads/CPU cores to use. Default 1.
- `OLLAMA_MODEL_TYPE`: Specifies the model type as `llama3`.

### Container Behavior
- `pull_policy: always`: Always pulls the latest image when deploying.
- `restart: unless-stopped`: Automatically restarts the container unless explicitly stopped.

### Resource Allocation
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation
- Ollama can be run with GPU acceleration inside Docker containers for Nvidia compatible GPUs.
- The configuration process has been summed up in nvidia_install.sh
- chmod +x nvidia_install.sh
- ./nvidia_install.sh

This configuration optimizes Ollama for GPU-accelerated inference while providing fine-grained control over resource usage and model behavior.

## Main Resources:
1. https://ollama.com/download/linux
2. https://github.com/rawanalkurd/Generative-AI-DSPy/blob/main/Running%20LLMs%20Locally%20A%20Guide%20to%20Setting%20Up%20Ollama%20with%20Docker.ipynb
3. https://github.com/rolfhelder/ollama-docker-compose/blob/main/docker-compose.yaml
4. https://secretdatascientist.com/ollama-cheatsheet/

## Planned Improvements
1. Trigger emojis and actions (dance, wave) where appropriate within conversations
2. Random assortments of igloo furniture to simulate igloo designs
3. Additional contexts added to the API message (i.e., ninja status, room name)
