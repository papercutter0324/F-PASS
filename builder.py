import session_config
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to INFO in production
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# List of placeholders
PLACEHOLDERS = {
    "hostname": "Fedora40",
}

def build_system_upgrade(options: Dict[str, Any], output_mode: str) -> str:
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""
    
    upgrade_commands = [
        "log_message \"Performing system upgrade... This may take a while...\"",
        f"dnf upgrade -y{quiet_redirect}",
        ""  # Add an empty line for readability
    ]
    
    return "\n".join(upgrade_commands)

def should_quiet_redirect(cmd: str) -> bool:
    no_redirect_patterns = [
        "log_message",
        "echo",
        "printf",
        "read",
        "prompt_",
        "EOF"
    ]
    # Check if the command starts with any of the patterns or contains "EOF"
    return not any(cmd.startswith(pattern) or "EOF" in cmd for pattern in no_redirect_patterns)

# Add this function to check dependencies
def check_dependencies(distro_data: Dict[str, Any]) -> Dict[str, Any]:
    # Check if multimedia codecs or GPU codecs are selected
    if any([
        distro_data["system_config"]["additional_codecs"]["apps"].get("install_multimedia_codecs", {}).get("selected", False),
        distro_data["system_config"]["additional_codecs"]["apps"].get("install_intel_codecs", {}).get("selected", False),
        distro_data["system_config"]["additional_codecs"]["apps"].get("install_amd_codecs", {}).get("selected", False)
    ]):
        # Ensure RPM Fusion is enabled
        distro_data["system_config"]["recommended_settings"]["apps"]["enable_rpmfusion"]["selected"] = True
    
    return distro_data

# Modify the build_system_config function
def build_system_config(distro_data: Dict[str, Any], output_mode: str) -> str:
    distro_data = check_dependencies(distro_data)
    config_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    system_config = distro_data.get("system_config", {}) # Extract just the system_config section of distro_data

    for subcategory_key, subcategory_value in system_config.items(): # Iterate through each subcategory in system_config
        if isinstance(subcategory_value, dict):
            # Get the "apps" dictionary within the subcategory
            apps = subcategory_value.get("apps", {})

            for app_key, app_data in apps.items(): # Iterate through each app in the apps dictionary
                if isinstance(app_data, dict):
                    if app_data.get("selected", False): # Check if the app is selected
                        description = app_data.get("description", "")
                        config_commands.append(f"# {description}")

                        # Handle commands based on installation type
                        install_type = app_data.get("installation_type")
                        commands = app_data.get("installation_types", {}).get(install_type, {}).get("command", None)

                        if commands is None: # Handle case where command is not found in installation_types
                            commands = app_data.get("command")

                        if isinstance(commands, str):
                            cmd = commands
                            if app_key == "set_hostname" and "hostnamectl set-hostname" in cmd:
                                hostname = distro_data["system_config"]["recommended_settings"]["hostname"] or PLACEHOLDERS.get('hostname', 'localhost')
                                cmd = f"{cmd} {hostname}"
                            if output_mode == "Quiet" and should_quiet_redirect(commands):
                                commands += quiet_redirect
                            config_commands.append(commands)
                        elif isinstance(commands, list):
                            for cmd in commands:                            
                                if app_key == "set_hostname" and "hostnamectl set-hostname" in cmd:
                                    hostname = distro_data["system_config"]["recommended_settings"]["hostname"] or PLACEHOLDERS.get('hostname', 'localhost')
                                    cmd = f"{cmd} {hostname}"
                                if output_mode == "Quiet" and should_quiet_redirect(cmd):
                                    cmd += quiet_redirect # Append each command with redirection if applicable
                                config_commands.append(cmd)
                        config_commands.append("") # Add an empty line for readability

    return "\n".join(config_commands)

def build_app_install(distro_data: Dict[str, Any], output_mode: str) -> str:
    install_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    # Iterate through the top-level categories and their subcategories
    for options_category, options_category_content in distro_data.items():
        if options_category == "custom_script" or options_category == "system_config":
            continue

        if not isinstance(options_category_content, dict):
            logging.warning(f"Expected dictionary for category content, got {type(options_category_content).__name__} for category {options_category}")
            logging.warning(f"Category content: {options_category_content}")
            continue

        for options_subcategory, options_subcategory_content in options_category_content.items():
            # Only process subcategories containing a dictionary and apps
            if isinstance(options_subcategory_content, dict) and 'apps' in options_subcategory_content:
                # Ensure 'apps' is a dictionary
                apps_content = options_subcategory_content['apps']
                if not isinstance(apps_content, dict):
                    logging.warning(f"Expected dictionary for apps content, got {type(apps_content).__name__} in subcategory {options_subcategory}")
                    continue

                # Collect selected apps
                category_apps = [app_id for app_id, app_data in apps_content.items() if app_data.get('selected', False)]
                
                if category_apps:
                    # Add a header for the current subcategory
                    install_commands.append(f"# Install {options_subcategory_content['name']} applications")

                    for app_id in category_apps:
                        app_data = apps_content.get(app_id, {})
                        if not isinstance(app_data, dict):
                            logging.warning(f"Expected dictionary for app data, got {type(app_data).__name__} for app_id {app_id}")
                            continue

                        install_commands.append(f"log_message \"Installing {app_data['name']}...\"")
                        
                        # Handle if there are multiple installation types
                        if 'installation_types' in app_data and app_data.get('installation_type'):
                            logging.warning(f"{app_id} install-types present")
                            logging.warning(f"{app_data.get('installation_type')}")
                            install_type = app_data.get('installation_type')
                            if install_type and install_type in app_data['installation_types']:
                                commands = app_data['installation_types'][install_type]['command']
                            else:
                                logging.warning(f"No valid installation type selected for {app_data['name']}")
                                continue
                        else:
                            # If there's no 'installation_types', fall back to a default 'command' if available
                            commands = app_data.get("command", "")
                            if not commands:
                                logging.warning(f"No command found for {app_data['name']}")
                                continue

                        # Add commands with quiet_redirect when applicable
                        if isinstance(commands, list):
                            for cmd in commands:
                                install_commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
                        else:
                            install_commands.append(f"{commands}{quiet_redirect if should_quiet_redirect(commands) else ''}")

                        install_commands.append(f"log_message \"{app_data['name']} installed successfully.\"")
                    
                    # Add an empty line for improved readability
                    install_commands.append("")

    return "\n".join(install_commands)

def build_custom_script(options: Dict[str, Any], output_mode: str) -> str:
    custom_script = options.get("custom_script", "").strip()
    if custom_script:
        return f"{custom_script}\n"
    return ""