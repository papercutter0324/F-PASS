from typing import Dict, Any

def build_system_upgrade(options: Dict[str, Any], output_mode: str) -> str:
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""
    
    upgrade_commands = [
        ('generate_log "Performing initial setup steps:\n'
         '   1. Installing dnf-plugins-core\n'
         '   2. Enabling Flathub repo\n'
         '   3. Performing system upgrade\n'
         'Please be patient. This may take a while."\n'),
        f"dnf -y install dnf-plugins-core{quiet_redirect}",
        f"flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo{quiet_redirect}",
        f"dnf -y upgrade{quiet_redirect}",
    ]
    
    return "\n".join(upgrade_commands)

def should_quiet_redirect(cmd: str) -> bool:
    no_redirect_patterns = ["generate_log", "echo", "printf", "read", "prompt_", "EOF"]
    # Check if the command starts with any of the patterns or contains "EOF" anywhere in the cmd
    return not any(cmd.startswith(pattern) or "EOF" in cmd for pattern in no_redirect_patterns)

def check_dependencies(distro_data: Dict[str, Any]) -> Dict[str, Any]:
    multimedia_codecs = distro_data["system_config"]["multimedia_codecs"]["apps"]
    if any(app.get("selected", False) for app in multimedia_codecs.values()):
        distro_data["system_config"]["useful_repos"]["apps"]["enable_rpmfusion"]["selected"] = True
    
    if multimedia_codecs["install_nvidia_codecs"]["selected"]:
        distro_data["system_config"]["useful_repos"]["apps"]["enable_nvidia_driver"]["selected"] = True
    return distro_data

def build_system_config(distro_data: Dict[str, Any], output_mode: str) -> str:
    def get_commands(app_data: dict) -> list[str]:
        # Extract commands from app_data, handling installation types and redirection.
        commands = app_data.get("installation_types", {}).get(app_data.get("installation_type"), {}).get("command", app_data.get("command", ""))
        return [commands] if isinstance(commands, str) else commands
    
    def process_command(distro_data: Dict, output_mode: str, cmd: str, app_key: str) -> str:
        if app_key == "set_hostname" and "hostnamectl set-hostname" in cmd:
            cmd += f" {distro_data['system_config']['recommended_settings']['apps']['set_hostname']['entered_name']}"
        
        return cmd + (" > /dev/null 2>&1" if output_mode == "Quiet" and should_quiet_redirect(cmd) else "")
    
    distro_data = check_dependencies(distro_data)
    config_commands = []

    for subcategory_value in distro_data.get("system_config", {}).values(): # Iterate through each subcategory in system_config
        if isinstance(subcategory_value, dict):
            apps = subcategory_value.get("apps", {})
            for app_key, app_data in apps.items():
                if isinstance(app_data, dict) and app_data.get("selected", False):
                    config_commands.append(f"# {app_data.get("description", "")}")
                    for cmd in get_commands(app_data):
                        config_commands.append(process_command(distro_data, output_mode, cmd, app_key))
                    config_commands.append("")  # Empty line for readability
                    config_commands.append("# Refreshing all repositories before beginning app installation.")
                    config_commands.append("dnf -y upgrade")
                    config_commands.append("")  # Empty line for readability

    return "\n".join(config_commands)

def build_app_install(distro_data: Dict[str, Any], output_mode: str) -> str:
    def get_commands(app_data: Dict[str, Any], quiet_redirect: str) -> list[str]:
        commands = []
        
        # Determine if 'command' or 'installation_types.command' is to be used
        command = app_data.get('installation_types', {}).get(app_data.get('installation_type'), {}).get('command', app_data.get('command'))
        
        if not command:
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
        if options_category not in {"custom_script", "system_config"}:
            for options_subcategory_content in options_category_content.values():
                if isinstance(options_subcategory_content, dict):
                    apps_content = options_subcategory_content.get('apps', {})
                    selected_apps = {app_id: app_data for app_id, app_data in apps_content.items() if app_data.get('selected', False)}

                    if selected_apps:
                        install_commands.append(f"# Install {options_subcategory_content.get('name', 'unknown')} applications")

                        # Generate commands for each selected app
                        for app_data in selected_apps.values():
                            install_commands.append(f"generate_log \"Installing {app_data.get('name', 'unknown')}...\"")
                            install_commands.extend(get_commands(app_data, quiet_redirect))
                            install_commands.append(f"generate_log \"{app_data.get('name', 'unknown')} installed successfully.\"")
                    
                        install_commands.append("")  # Empty line for readability

    return "\n".join(install_commands)

def build_custom_script(options: Dict[str, Any], output_mode: str) -> str:
    custom_script = options.get("custom_script", "").strip()
    if custom_script:
        return f"{custom_script}\n"
    return ""