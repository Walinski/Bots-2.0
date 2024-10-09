#!/bin/bash

# Set the directory where docker-compose.yml is located
FOLDER=wand
WAND_DIR="$(dirname "$(realpath "$0")")"



# Function to print text in red
magenta_echo() {
  local message=$1
  echo -e "\n\e[35m${message}\e[0m\n"
}

yellow_echo() {
  local message=$1
  echo -e "\e[33m${message}\e[0m\n"
}

green_echo() {
  local message=$1
  echo -e "\e[32m${message}\e[0m\n"
}

# Function to check if Docker is installed
check_docker_installed() {
  if ! command -v docker &> /dev/null; then
    magenta_echo "Docker is not installed."
    exit 1
  fi
}


# Used to avoid repeatedly entering the sudo password
handle_docker_privileges() { 
  if ! getent group docker >/dev/null; then
    magenta_echo "Docker group does not exist. Creating 'docker' group..."
    sudo groupadd docker
  fi

  # Check if the current user is in the 'docker' group
  if groups $USER | grep &>/dev/null "\bdocker\b"; then
    return 0
  else
    # Prompt the user for confirmation to add them to the 'docker' group
    read -p "User '$USER' is not in the 'docker' group. Would you like to add '$USER' to the 'docker' group? (y/n): " choice
    case "$choice" in 
      y|Y ) 
        sudo usermod -aG docker $USER
        magenta_echo "$USER has been added to the 'docker' group for executing commands."
        magenta_echo "Please log out and log back in for the changes to take effect."
        ;;
      n|N ) 
        magenta_echo "User '$USER' was not added to the 'docker' group."
        ;;
      * ) 
        magenta_echo "Invalid input. Please enter 'Y' or 'N'."
        ;;
    esac
  fi
}


yellow_numbers() {
  echo -ne "\e[33m$1\e[0m"
}

green_names() {
  echo -ne "\e[32m$1\e[0m"
}


enable_log_view() {
  # Ensure Windows Terminal is available
  if ! command -v wt.exe &> /dev/null; then
    magenta_echo "Windows Terminal (wt.exe) is not installed or not in the PATH."
    return 1
  fi

  # Check for running Docker containers
  containers=$(docker ps --format "{{.Names}}")
  if [ -z "$containers" ]; then
    magenta_echo "No active Docker containers found."
    return 0
  fi

  # Display available Docker containers with numbers
  echo -e "\nAvailable Docker containers:\n"
  IFS=$'\n' read -rd '' -a container_array <<< "$containers" # Read the containers into an array
  for i in "${!container_array[@]}"; do
	green_names "${container_array[i]}"
	yellow_numbers " - ($((i + 1)))" 
	echo 
  done

  # Prompt user to select a container by number
  echo 
  read -p "Enter the number to view logs: " container_number
  
  if ! [[ "$container_number" =~ ^[0-9]+$ ]] || [ "$container_number" -lt 1 ] || [ "$container_number" -gt "${#container_array[@]}" ]; then
    magenta_echo "Invalid selection. Please enter a valid number."
    return 1
  fi

  # Extract the selected container name using the user-provided number
  container_name="${container_array[$((container_number - 1))]}"

  # Ask if the user wants to filter by keywords
  read -p "Would you like to filter logs to keywords? (Y/N): " filter_choice
  filter_choice=$(echo "$filter_choice" | tr '[:upper:]' '[:lower:]') # Convert to lowercase

  if [[ "$filter_choice" == "y" ]]; then
    # Prompt the user for keywords to filter logs
    read -p "Enter keywords to filter logs (separated by space): " -a keywords

    # Ask if the filter should be inclusion or exclusion
    read -p "Should the filter be including (I) or excluding (E)? (I/E): " filter_type
    filter_type=$(echo "$filter_type" | tr '[:upper:]' '[:lower:]') # Convert to lowercase

    if [[ "$filter_type" == "e" ]]; then
      grep_option="-v"  # Exclusion filter
    else
      grep_option=""    # Inclusion filter
    fi

    # Prepare the grep pattern for filtering logs
    grep_pattern=$(printf "|%s" "${keywords[@]}")
    grep_pattern=${grep_pattern:1}  # Remove the leading '|'

    yellow_echo "\nBeginning $container_name using $grep_option and $grep_pattern"	

    # Command to run with filtering
    command="cd $WAND_DIR && docker logs -f $container_name | grep $grep_option -E '$grep_pattern'"
  else
    command="cd $WAND_DIR && docker logs -f $container_name"
  fi

  # Open a new tab in Windows Terminal, set the tab title to the container name, and run the docker logs command with grep filters
  powershell.exe -Command "wt.exe -w 0 nt --title \"$container_name\" -d . wsl.exe bash -c \"$command\""
}



# Function to clear Redis cache
clear_redis_cache() {
  docker exec ${FOLDER}-redis-1 redis-cli FLUSHALL
  magenta_echo "Redis cache cleared."
}

# Function to stop and remove all Docker containers
shutdown_all_containers() {
  magenta_echo "Stopping and removing all containers..."
  docker stop $(docker ps -q)
  docker rm $(docker ps -aq)
  magenta_echo "Docker containers have been stopped and removed."
}




docker_compose() {

  # Ensure Windows Terminal is available
  if ! command -v wt.exe &> /dev/null; then
    magenta_echo "Windows Terminal (wt.exe) is not installed or not in the PATH."
    return 1
  fi

  # Check if the Docker containers are already up, but silence the output
  cd "$WAND_DIR" || { magenta_echo "Failed to navigate to $WAND_DIR. Exiting."; return 1; }
  
  if docker-compose ps | grep 'Up' > /dev/null 2>&1; then
    magenta_echo "\nDocker containers are already running."
    return 0
  fi

  # Start Docker containers in a new Windows Terminal tab
  powershell.exe -Command "wt.exe -w 0 nt -d . wsl.exe bash -c \"cd $WAND_DIR && docker-compose up -d && bash\""

  magenta_echo "Docker containers beginning in a new tab in Windows Terminal."

}


docker_compose_down() {
  # Check if any Docker containers are running FIRST
  if docker-compose ps | grep 'Up' > /dev/null 2>&1; then
    docker-compose down
  else
    magenta_echo "Server is shutdown!"
  fi
}


CDWand() {
  powershell.exe -Command "wt.exe nt -d . wsl.exe bash -c \"cd $WAND_DIR && bash\"" # shorthand for new-tab
}


# Function to display a menu with options
show_menu() {
  yellow_echo "\nPlease select an option:"
  yellow_echo "1) Purge Redis Cache"
  yellow_echo "2) Stop ALL Containers"
  yellow_echo "3) View/Filter Logs"
  yellow_echo "4) Begin Wand"
  yellow_echo "5) End Wand"
  yellow_echo "6) Navigate to Directory"
  yellow_echo "7) Cancel"
}



# Function to check and manage Docker containers for SoleroHoudini
setup_solero_containers() {

  while true; do
	show_menu
    read -p "Enter your choice [1-5]: " choice
  
    case $choice in
      1)
        clear_redis_cache
        ;;
      2)
        shutdown_all_containers
        ;;
      3)
        enable_log_view
        ;;
      4)
        docker_compose
        ;;
      5)
        docker_compose_down
        ;;	
      6)
        CDWand
        ;;			
      7)
        magenta_echo "Exiting..."
        break
        ;;
      *)
        magenta_echo "Invalid option. Please select a valid option from the menu."
        ;;
    esac
  done
  
}

# Main script execution
handle_docker_privileges
check_docker_installed
setup_solero_containers
