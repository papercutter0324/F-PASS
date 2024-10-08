#!/bin/bash
# F-Pass - Fedora Post-Installation Automated Setup Script

# Ensure script is run using sudo
[ "$EUID" -eq 0 ] || { echo "This command must be run using sudo."; exit 1; }

# Set variables
ACTUAL_USER=$SUDO_USER
ACTUAL_HOME=$(eval echo ~$SUDO_USER)
LOG_FILE="/var/log/F-PASS.log"

get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

generate_log() {
    local message="$1"
    echo "$(get_timestamp) - $message" | tee -a "$LOG_FILE"
}

error_handler() {
    local exit_code=$?; local message="$1"
    [ $exit_code -eq 0 ] || { generate_log "ERROR: $message"; exit $exit_code; }
}

request_restart() {
    sudo -u $ACTUAL_USER bash -c 'read -p "Your computer must restart to complete the process. Restart now? (y/n): " choice; [[ $choice == [yY] ]]'
    [ $? -eq 0 ] && generate_log "Rebooting." && reboot || generate_log "Reboot cancelled."
}

# Function to backup files
backup_file() {
    local file="$1"
    [ -f "$file" ] && cp "$file" "$file.bak" && { generate_log "Backed up $file"; } || error_handler "Failed to backup $file"
}

echo -e "";
echo -e "\e[34m      ╔════════════════════════════════════════════════╗\e[0m";
echo -e "\e[34m      ║ ███████╗░░░░░░██████╗░░█████╗░░██████╗░██████╗ ║\e[0m";
echo -e "\e[34m      ║ ██╔════╝░░░░░░██╔══██╗██╔══██╗██╔════╝██╔════╝ ║\e[0m";
echo -e "\e[34m      ║ █████╗░░█████╗██████╔╝███████║╚█████╗░╚█████╗░ ║\e[0m";
echo -e "\e[34m      ║ ██╔══╝░░╚════╝██╔═══╝░██╔══██║░╚═══██╗░╚═══██╗ ║\e[0m";
echo -e "\e[34m      ║ ██║░░░░░░░░░░░██║░░░░░██║░░██║██████╔╝██████╔╝ ║\e[0m";
echo -e "\e[34m      ║ ╚═╝░░░░░░░░░░░╚═╝░░░░░╚═╝░░╚═╝╚═════╝░╚═════╝░ ║\e[0m";
echo -e "\e[34m      ╚════════════════════════════════════════════════╝\e[0m";
echo "        Fedora Post-Installation Automated Setup Script";
echo "";
echo -e "       Do \e[1m\e[31mNOT\e[0m run this script unless build it yourself!";
echo "It changes system settings and installs a variety of programs.";
echo "";
echo -e "        \e[1m\e[31mONLY\e[0m run this script if you trust the source!";
echo "";
read -p "Press Enter to continue or CTRL+C to cancel."

{{system_config}}

{{system_upgrade}}

{{app_install}}

{{custom_script}}

echo "";
echo -e "\e[34m╔═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗\e[0m";
echo -e "\e[34m║ ░██████╗███████╗████████╗██╗░░░██╗██████╗░░░░█████╗░░█████╗░███╗░░░███╗██████╗░██╗░░░░░███████╗████████╗███████╗██╗ ║\e[0m";
echo -e "\e[34m║ ██╔════╝██╔════╝╚══██╔══╝██║░░░██║██╔══██╗░░██╔══██╗██╔══██╗████╗░████║██╔══██╗██║░░░░░██╔════╝╚══██╔══╝██╔════╝██║ ║\e[0m";
echo -e "\e[34m║ ╚█████╗░█████╗░░░░░██║░░░██║░░░██║██████╔╝░░██║░░╚═╝██║░░██║██╔████╔██║██████╔╝██║░░░░░█████╗░░░░░██║░░░█████╗░░██║ ║\e[0m";
echo -e "\e[34m║ ░╚═══██╗██╔══╝░░░░░██║░░░██║░░░██║██╔═══╝░░░██║░░██╗██║░░██║██║╚██╔╝██║██╔═══╝░██║░░░░░██╔══╝░░░░░██║░░░██╔══╝░░╚═╝ ║\e[0m";
echo -e "\e[34m║ ██████╔╝███████╗░░░██║░░░╚██████╔╝██║░░░░░░░╚█████╔╝╚█████╔╝██║░╚═╝░██║██║░░░░░███████╗███████╗░░░██║░░░███████╗██╗ ║\e[0m";
echo -e "\e[34m║ ╚═════╝░╚══════╝░░░╚═╝░░░░╚═════╝░╚═╝░░░░░░░░╚════╝░░╚════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚══════╝╚══════╝░░░╚═╝░░░╚══════╝╚═╝ ║\e[0m";
echo -e "\e[34m╚═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝\e[0m";
echo "";
generate_log "All steps completed. Enjoy!"

request_restart