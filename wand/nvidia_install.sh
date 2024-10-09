#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to update /etc/docker/daemon.json
update_docker_daemon_json() {
    DAEMON_JSON="/etc/docker/daemon.json"
    NVIDIA_RUNTIME_CONFIG='{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}'

    if [ -f "$DAEMON_JSON" ]; then
        # Backup existing daemon.json
        sudo cp "$DAEMON_JSON" "$DAEMON_JSON.bak"
        # Merge existing configuration with NVIDIA runtime configuration
        sudo jq '.runtimes.nvidia = {
          "path": "nvidia-container-runtime",
          "runtimeArgs": []
        }' "$DAEMON_JSON" | sudo tee "$DAEMON_JSON" > /dev/null
    else
        # Create new daemon.json with NVIDIA runtime configuration
        echo "$NVIDIA_RUNTIME_CONFIG" | sudo tee "$DAEMON_JSON" > /dev/null
    fi
}

# Check if nvidia-container-toolkit is installed
if command_exists nvidia-container-toolkit; then
    echo "NVIDIA Container Toolkit is already installed."
else
    echo "NVIDIA Container Toolkit is not installed. Installing now..."

    # Configure the production repository
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    # Update the packages list from the repository
    sudo apt-get update

    # Install the NVIDIA Container Toolkit packages
    sudo apt-get install -y nvidia-container-toolkit

    echo "NVIDIA Container Toolkit installation completed."
fi

# Update Docker daemon.json to add NVIDIA runtime
update_docker_daemon_json

# Restart Docker to apply changes
sudo systemctl daemon-reload
sudo systemctl restart docker

echo "Docker daemon configuration updated and Docker restarted."

