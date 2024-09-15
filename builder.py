from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to INFO in production
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def build_system_upgrade(options: Dict[str, Any], output_mode: str) -> str:
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""
    
    upgrade_commands = [
        ('generate_log "Performing initial setup steps:\n'
         '   1. Installing dnf-plugins-core\n'
         '   2. Enabling Flathub repo\n'
         '   3. Performing system upgrade\n\n'
         'Please be patient. This may take a while."'),
        f"dnf -y install dnf-plugins-core{quiet_redirect}",
        f"flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo{quiet_redirect}",
        f"dnf -y upgrade{quiet_redirect}",
        ""  # Add an empty line for readability
    ]
    
    return "\n".join(upgrade_commands)

def should_quiet_redirect(cmd: str) -> bool:
    no_redirect_patterns = ["generate_log", "echo", "printf", "read", "prompt_", "EOF"]
    # Check if the command starts with any of the patterns or contains "EOF"
    return not any(cmd.startswith(pattern) or "EOF" in cmd for pattern in no_redirect_patterns)

def check_dependencies(distro_data: Dict[str, Any]) -> Dict[str, Any]:
    additional_codecs = distro_data["system_config"]["additional_codecs"]["apps"]
    if any([
        additional_codecs.get("install_multimedia_codecs", {}).get("selected", False),
        additional_codecs.get("install_intel_codecs", {}).get("selected", False),
        additional_codecs.get("install_nvidia_codecs", {}).get("selected", False),
        additional_codecs.get("install_amd_codecs", {}).get("selected", False)
    ]):
        distro_data["system_config"]["recommended_settings"]["apps"]["enable_rpmfusion"]["selected"] = True
    
    return distro_data

def build_system_config(distro_data: Dict[str, Any], output_mode: str) -> str:
    def get_commands(app_data: dict) -> list[str]:
        # Extract commands from app_data, handling installation types and redirection.
        install_type = app_data.get("installation_type")
        commands = app_data.get("installation_types", {}).get(install_type, {}).get("command", app_data.get("command", ""))
        if isinstance(commands, str):
            commands = [commands]
        return commands
    
    def process_command(distro_data: Dict, output_mode: str, quiet_redirect: str, cmd: str, app_key: str) -> str:
        # Prepare command by adding hostname and quiet redirection if needed.
        logging.warning(f"app_key: {app_key}")
        if app_key == "set_hostname" and "hostnamectl set-hostname" in cmd:
            logging.warning(f"Replacing hostname with: {distro_data['system_config']['recommended_settings']['apps']['set_hostname']['entered_name']}")
            hostname = distro_data['system_config']['recommended_settings']['apps']['set_hostname']['entered_name']
            cmd = f"{cmd} {hostname}"

        if output_mode == "Quiet" and should_quiet_redirect(cmd):
            cmd += quiet_redirect
        return cmd
    
    distro_data = check_dependencies(distro_data)
    config_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    system_config = distro_data.get("system_config", {})

    for subcategory_value in system_config.values(): # Iterate through each subcategory in system_config
        if isinstance(subcategory_value, dict):
            apps = subcategory_value.get("apps", {})
            for app_key, app_data in apps.items():
                if isinstance(app_data, dict) and app_data.get("selected", False):
                    description = app_data.get("description", "")
                    config_commands.append(f"# {description}")

                    commands = get_commands(app_data)
                    for cmd in commands:
                        cmd = process_command(distro_data, output_mode, quiet_redirect, cmd, app_key)
                        config_commands.append(cmd)

                    config_commands.append("")  # Add an empty line for readability

    return "\n".join(config_commands)

def build_app_install(distro_data: Dict[str, Any], output_mode: str) -> str:
    def get_commands(app_data: Dict[str, Any], quiet_redirect: str) -> list[str]:
        commands = []
        # Get the appropriate command(s)
        install_type = app_data.get('installation_type')
        command = (app_data.get('installation_types', {}).get(install_type, {}).get('command') 
                   if install_type else app_data.get('command'))

        if not command:
            logging.warning(f"No command found for {app_data.get('name', 'unknown app')}")
            return []

        # Normalize to a list of commands
        command_list = command if isinstance(command, list) else [command]

        # Add quiet redirect where applicable
        for cmd in command_list:
            if "SELECTEDSWAPSIZE" in cmd:
                cmd = cmd.replace ("SELECTEDSWAPSIZE", distro_data["advanced_settings"]["system_settings"]["apps"]["extra_swap_space"]["entered_size"])

            commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
        
        return commands
    
    install_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    # Iterate through the top-level categories and their subcategories
    for options_category, options_category_content in distro_data.items():
        if options_category in {"custom_script", "system_config"}:
            continue

        for options_subcategory_content in options_category_content.values():
            if not isinstance(options_subcategory_content, dict) or 'apps' not in options_subcategory_content:
                continue
        
            apps_content = options_subcategory_content['apps']
            if not isinstance(apps_content, dict):
                logging.warning(f"Expected dictionary for apps content, got {type(apps_content).__name__}")
                continue
            
            # Collect and process selected apps
            selected_apps = [app_id for app_id, app_data in apps_content.items() if isinstance(app_data, dict) and app_data.get('selected', False)]

            if not selected_apps:
                continue

            install_commands.append(f"# Install {options_subcategory_content.get('name', 'unknown')} applications")

            for app_id in selected_apps:
                app_data = apps_content.get(app_id, {})
                if not isinstance(app_data, dict):
                    logging.warning(f"Expected dictionary for app data, got {type(app_data).__name__} for app_id {app_id}")
                    continue

                install_commands.append(f"generate_log \"Installing {app_data.get('name', 'unknown')}...\"")
                install_commands.extend(get_commands(app_data, quiet_redirect))
                install_commands.append(f"generate_log \"{app_data.get('name', 'unknown')} installed successfully.\"")
            
            install_commands.append("")  # Add an empty line for readability

    return "\n".join(install_commands)

def build_custom_script(options: Dict[str, Any], output_mode: str) -> str:
    custom_script = options.get("custom_script", "").strip()
    if custom_script:
        return f"{custom_script}\n"
    return ""