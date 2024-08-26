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

log_message() {
    local message="$1"
    echo "$(get_timestamp) - $message" | tee -a "$LOG_FILE"
}

error_handler() {
    local exit_code=$?; local message="$1"
    [ $exit_code -eq 0 ] ||; { log_message "ERROR: $message"; exit $exit_code; }
}

request_restart() {
    sudo -u $ACTUAL_USER bash -c 'read -p "Your computer must restart to complete the process. Restart now? (y/n): " choice; [[ $choice == [yY] ]]'
    [ $? -eq 0 ] && log_message "Rebooting." && reboot || log_message "Reboot cancelled."
}

# Function to backup configuration files
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "$file.bak"
        error_handler "Failed to backup $file"
        log_message "Backed up $file"
    fi
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
echo -e "\e[34m        Fedora Post-Installation Automated Setup Script\e[0m";
echo "";
echo -e "       Do \e[1m\e[31mNOT\e[0m run this script unless build it yourself!";
echo "It changes system settings and installs a variety of programs.";
echo "";
echo -e "        \e[1m\e[31mONLY\e[0m run this script if you trust the source!";
echo "";
read -p "Press Enter to continue or CTRL+C to cancel."

{{system_upgrade}}

{{system_config}}

{{app_install}}

{{custom_script}}

# Finish
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
log_message "All steps completed. Enjoy!"

# Prompt user to restart
request_restart
