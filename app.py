# Welcome to the F-PASS
# Fedora Post-Installation Automated Setup Script
#
# This tool is designed to help you generate a script you can run after completing the
# intial installation of Fedora. It make's use of a Streamlit-based web interface to
# simplify generating a script that will automate configuration of some key settings
# and drivers and install a selection of useful programs. The goal is to offer a 
# one-file # solution to get you all set up and running after performing a fresh
# installation.
#
# Originally a fork of Karl Stefan Danisz's [Fedora Workstation NATTD Not Another "Things
# To Do"!]. Much of the code has be rewritten, slowly growing into a project all of its
# own. You can check out the orginal version at his github repository:
# https://github.com/k-mktr/fedora-things-to-do/
#
# This script is licensed under the GNU General Public License v3.0
#
import streamlit as st # type: ignore
from typing import Dict, Any
import builder
import logging
import json
import re

# Constants
SCRIPT_TEMPLATE = 'template.sh'
DNF_OR_FLATPAK_OPTIONS = [('dnf', 'DNF'), ('flatpak', 'Flatpak')]
DNF_OR_FLATPAK_OR_APPIMAGE_OPTIONS = [('dnf', 'DNF'), ('flatpak', 'Flatpak'), ('appimage', 'AppImage')]
VIRTUALBOX_OPTIONS = [('without_extension', 'VirtualBox Only'), ('with_extension', 'VirtualBox & Extenstion Pack')]
DOCKER_OPTIONS = [('install_standard', 'Docker Only'), ('install_portainer', 'Docker & Portainer'), ('install_nvidia_toolkit', 'Docker & Nvidia Toolkit'), ('install_portainer_and_nvidia_toolkit', 'Docker & Both')]
FONT_OPTIONS = [('core', 'Core Fonts'), ('windows', 'Windows Fonts')]
DISK_OPTIONS = [('ssd', 'SSD'), ('hdd', 'HDD')]

st.set_page_config(
    page_title="F-Pass Creator",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "https://github.com/papercutter0324/F-PASS/issues",
        'About': """
        #### F-PASS   
        **Fedora Post-Installation Automated Setup Script**
        
        This tool will generate a script to automate the final steps of
        setting up a fresh Fedora Workstation installion. If you find this
        tool useful, feel free to share, suggest improvements, and propose
        changes.

        Created by papercutter0324

        GitHub: https://github.com/papercutter0324/F-PASS
        """
    }
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Change to INFO in production
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_template() -> str:
    with open(SCRIPT_TEMPLATE, 'r') as file:
        return file.read()

def add_selected_key(data: Dict[str, Any]) -> Dict[str, Any]:
    # Iterate over the dictionary
    for key, value in data.items():
        if isinstance(value, dict):
            # If the current dictionary contains 'apps', add 'selected' key to each app
            if 'apps' in value:
                for app_key, app_value in value['apps'].items():
                    # Ensure that each app entry has a 'selected' key
                    if 'selected' not in app_value:
                        app_value['selected'] = False  # Default value
            else:
                # Recursively apply to nested dictionaries
                add_selected_key(value)
    return data

def load_app_data(file_name: str) -> dict:
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"{file_name} not found!")
        return {}
    except json.JSONDecodeError:
        logging.error(f"{file_name} is not a valid JSON file!")
        return {}

def render_sidebar() -> Dict[str, Any]:
    # Centered, clickable logo to reload the page
    st.sidebar.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; padding: 10px;">
            <a href="/" target="_self">
                <img src="https://github.com/papercutter0324/F-PASS/blob/master/assets/logo.png?raw=true" width="240" alt="Logo">
            </a>
        </div>
        """, unsafe_allow_html=True)
    st.sidebar.header("Configuration Options")

    # Create a dictionary of supported distros, their matching json files
    supported_distros = {"Fedora 40": 'fedora_data.json'}
    selected_distro = st.sidebar.selectbox("Choose a Distribution", list(supported_distros.keys()), help="Load the list of options for your distro.")

    if selected_distro:
        distro_file = supported_distros[selected_distro]
    else: #Default to Fedora 40 if nothing has been selected
        distro_file = supported_distros["Fedora 40"]

    
    distro_data = load_app_data(distro_file) # Load the distro data
    distro_data = add_selected_key(distro_data) # Ensure all app entries have a 'selected' key

    output_mode = st.sidebar.selectbox(
        "Selected Terminal Output Mode",
        ["Verbose", "Quiet"],
        help="Determines how much information the terminal will display as the script runs."
    )

    # Generate the sidebar sections for the selected distro
    for options_category, disto_category_keys in distro_data.items():
        if distro_data.items() != "name":
            render_app_section(distro_data, options_category)

    with st.sidebar.expander("Advanced - Custom Script"): # Section for adding a custom script
        st.warning("""⚠️ **Caution**: Intended for advanced users. Incorrect shell commands can potentially harm your system or render it inoperable.  
                   Use with care!""")
        
        default_custom_text = '# Each command goes on a new line.'
        distro_data["custom_script"] = st.text_area(
            "Custom Commands:",
            value=default_custom_text,
            help="Enter any additional shell commands you want to run at the end of the script.",
            height=200,
            key="custom_script_input"
        )
        
        if distro_data["custom_script"].strip() != default_custom_text:
            st.info("Remember to review your custom commands in the script preview before downloading.")

    
    # Placeholder at the bottom of the sidebar
    sidebar_bottom = st.sidebar.empty()
    sidebar_bottom.markdown("""
    <style>
        .link-bar {
            display: flex;
            justify-content: center;
            animation: fadeIn 1s ease-out 0.9s;
            opacity: 0;
            animation-fill-mode: forwards;
            text-align: center;
        }
        .link-bar a {
            text-decoration: none;
            font-weight: bold;
            color: #8da9c4;
        }
        .link-bar a:hover {
            text-decoration: underline;
        }
        .separator {
            width: 100%;
            border-top: 1px solid #8da9c4;
            margin: 21px 0;
        }
        @media (max-width: 600px) {
            .link-bar {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
    <div class="separator"></div>
    <div class="link-bar">
        <img src="https://fedoraproject.org/assets/images/fedora-workstation-logo.png" alt="Fedora Logo" class="logo" width="240">
    </div>
    <div style="text-align: center;">
        <a href="https://fedoraproject.org/workstation/" target="_blank" style="text-decoration: none;" aria-label="Fedora Workstation">Grab the latest version of Fedora here.</a>
    </div>
    """, unsafe_allow_html=True)

    return distro_data, output_mode

def render_app_section(distro_data: Dict[str, Any], options_category: str) -> Dict[str, Any]:
    with st.sidebar.expander(distro_data[options_category]['name']):
        subcategories = list(distro_data[options_category].items())
        special_case_apps = {
            "set_hostname": handle_hostname,
            "enable_rpmfusion": handle_rpmfusion,
            "install_virtualbox": handle_special_installation_types,
            "install_docker_engine": handle_special_installation_types,
            "install_microsoft_fonts": handle_special_installation_types,
            "extra_swap_space": handle_swapspace
        }
        
        for options_subcategory, subcategory_data in subcategories:
            if options_subcategory == "name":
                continue
            
            st.subheader(subcategory_data['name'])
            
            for options_app, app_data in subcategory_data['apps'].items():
                app_selected = st.checkbox(
                    app_data['name'],
                    key=f"{options_category}_{options_subcategory}_apps_{options_app}",
                    help=app_data.get('description', '')
                )
                app_data['selected'] = app_selected

                if options_app in special_case_apps:
                    special_case_apps[options_app](
                        app_selected,
                        subcategory_data=subcategory_data,
                        options_category=options_category,
                        options_subcategory=options_subcategory,
                        options_app=options_app,
                        distro_data=distro_data
                    )
                else:
                    if app_selected and 'installation_types' in app_data:
                        installation_type = st.radio(
                            f"Choose {app_data['name']} installation type:",
                            list(app_data['installation_types'].keys()),
                            key=f"{options_category}_{options_subcategory}_apps_{options_app}_install_type"
                        )
                        subcategory_data['apps'][options_app]['installation_type'] = installation_type

                if app_selected and options_app not in {"set_hostname", "extra_swap_space"}:
                    handle_warnings_and_messages(options_app, distro_data)

    return distro_data

def handle_hostname(app_selected: bool, **kwargs):
    distro_data = kwargs.get('distro_data', {})
    hostname_data = distro_data.get("system_config", {}).get("recommended_settings", {}).get("apps", {}).get("set_hostname", {})
    
    if app_selected:
        entered_hostname = st.text_input("Enter the new hostname:")

        try:
            if is_valid_hostname(entered_hostname):
                logging.warning(f"Valid hostname entered")
                hostname_data["entered_name"] = entered_hostname
                logging.warning(f"Entered hostname: {entered_hostname}")
        except KeyError as e:
            logging.warning(f"KeyError: Missing expected key {e} in distro_data.")
        else:
            if hostname_data["entered_name"] == "":
                hostname_data["entered_name"] = hostname_data["default"]
                handle_warnings_and_messages("set_hostname", distro_data)

    logging.warning(f"New hostname is: {distro_data['system_config']['recommended_settings']['apps']['set_hostname']['entered_name']}")

def is_valid_hostname(hostname: str) -> bool:
    if not hostname or len(hostname) > 253:
        return False

    regex = re.compile(
        r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$'
        r'(\.[A-Za-z0-9-]{1,63})*$'
    )

    # Split hostname by dots and validate each label
    labels = hostname.split('.')
    return all(regex.match(label) for label in labels)

def handle_swapspace(app_selected: bool, **kwargs):
    subcategory_data = kwargs['subcategory_data']
    options_category = kwargs['options_category']
    options_subcategory = kwargs['options_subcategory']
    options_app = kwargs['options_app']
    distro_data = kwargs.get('distro_data', {})
    swap_data = distro_data.get("advanced_settings", {}).get("system_settings", {}).get("apps", {}).get("extra_swap_space", {})

    if app_selected:
        entered_size = st.text_input("Enter the desired swap size in GB: (Max: 32)")

        try:
            if entered_size.strip() and 1 <= int(entered_size) <= 32:
                swap_data["entered_size"] = f"{int(entered_size)}G"
                handle_special_installation_types(
                        "extra_swap_space",
                        subcategory_data=subcategory_data,
                        options_category=options_category,
                        options_subcategory=options_subcategory,
                        options_app=options_app,
                        distro_data=distro_data
                    )
            else:
                # Handle the case where input is invalid but not an exception
                swap_data["entered_size"] = swap_data["default"]
                handle_warnings_and_messages("extra_swap_space", distro_data)
        except ValueError:
            swap_data["entered_size"] = swap_data["default"]
            handle_warnings_and_messages("extra_swap_space", distro_data)
        
def handle_rpmfusion(app_selected: bool, **kwargs):
    distro_data = kwargs['distro_data']

    if app_selected:
        distro_data["system_config"]["recommended_settings"]["apps"]["enable_rpmfusion"]["selected"] = app_selected

def handle_special_installation_types(app_selected: bool, **kwargs):
    subcategory_data = kwargs['subcategory_data']
    options_category = kwargs['options_category']
    options_subcategory = kwargs['options_subcategory']
    options_app = kwargs['options_app']

    if options_app == "install_virtualbox":
        install_type_title = "VirtualBox Extension Pack"
        install_options = VIRTUALBOX_OPTIONS
        help_text = "Select if you wish to download the VirtualBox Extension Pack."
    elif options_app == "install_docker_engine":
        install_type_title = "Docker Installation Options"
        install_options = DOCKER_OPTIONS
        help_text = "Select if you wish to install Portainer and/or the Nvidia container toolkit."
    elif options_app == "install_microsoft_fonts":
        install_type_title = "Windows Font Groups"
        install_options = FONT_OPTIONS
        help_text = "Choose how to install Windows fonts."
    elif options_app == "extra_swap_space":
        install_type_title = "Select Disk Type:"
        install_options = DISK_OPTIONS
        help_text = "Choose the type of drive being used."
    
    if app_selected:
        app_key = f"{options_category}_{options_subcategory}_apps_{options_app}_install_type"
        installation_type = render_installation_type_selector(install_type_title, install_options, app_key, help_text)
        subcategory_data['apps'][options_app]['installation_type'] = installation_type

def render_installation_type_selector(install_type_title: str, install_options: list, app_key:str, help_text: str) -> str:
    return st.radio(
        install_type_title,
        [opt[0] for opt in install_options],  # Extract the values for the radio buttons
        format_func=lambda x: dict(install_options).get(x, x),  # Format the label based on the selected value
        key=app_key,
        help=help_text
    )

def handle_warnings_and_messages(options_app: str, distro_data: Dict[str, Any]):
    if options_app == "set_hostname":
        default_hostname = distro_data.get("system_config", {}).get("recommended_settings", {}).get("apps", {}).get("set_hostname", {}).get("default", {})
        st.warning(
            "Invalid hostname.  \n"
            f"Using default: \"{default_hostname}\"\n"
            "- Use only letters, digits, and hyphens\n"
            "- Start and end with letters or digits\n"
            "- Each label may be 1 to 63 characters\n"
            "- Multiple labels permitted, separated by a period\n"
            "- Total max of 253 characters"
        )
    elif options_app in ["install_multimedia_codecs", "install_intel_codecs", "install_nvidia_codecs", "install_amd_codecs"]:
        if distro_data["system_config"]["recommended_settings"]["apps"]["enable_rpmfusion"]["selected"] == False:
            st.markdown("""
                ```
                RPM Fusion has been enabled  
                due to codec dependencies.
                ```
            """)
            distro_data["system_config"]["recommended_settings"]["apps"]["enable_rpmfusion"]["selected"] = True
    elif options_app == "install_virtualbox":
        if distro_data['virtualization_apps']['virtualization_apps']['apps']['install_virtualbox']['installation_type'] == "with_extension":
            st.warning("⚠️ The extension pack will be saved in your downloads folder. You will still need to manually install it as normal.")
    elif options_app == "install_docker_engine":
            st.warning("⚠️ During installation, Docker's GPG key will automatically be imported.")
            st.markdown("[You can verify Docker's GPG key here](https://docs.docker.com/engine/install/fedora/)")
    elif options_app == "install_enpass":
        st.warning("⚠️ During installation, Enpass's YUM repository will automatically be imported.")
    elif options_app == "install_microsoft_fonts":
        if distro_data['customization']['fonts']['apps']['install_microsoft_fonts']['installation_type'] == "windows":
            st.warning("⚠️ This method requires a valid Windows license. "
                       "Please ensure you comply with Microsoft's licensing terms.")
            st.markdown("[Learn more about Windows fonts licensing](https://learn.microsoft.com/en-us/typography/fonts/font-faq)")
    elif options_app == "extra_swap_space":
        st.warning("Invalid value. Please enter a number between 1 and 32.")

def build_script(distro_data: Dict[str, Any], output_mode: str) -> str:
    if distro_data["custom_script"] == "# Each command goes on a new line.":
        script_parts = {
            "system_upgrade": builder.build_system_upgrade(distro_data, output_mode),
            "system_config": builder.build_system_config(distro_data, output_mode),
            "app_install": builder.build_app_install(distro_data, output_mode),
        }
    else: 
        script_parts = {
            "system_upgrade": builder.build_system_upgrade(distro_data, output_mode),
            "system_config": builder.build_system_config(distro_data, output_mode),
            "app_install": builder.build_app_install(distro_data, output_mode),
            "custom_script": builder.build_custom_script(distro_data, output_mode),
        }

    preview_script = f"(...)  # Script header\n\n# Selected distro: {distro_data['system_config']['recommended_settings']['apps']['set_hostname']['default']}\n# Output Mode: {output_mode}\n\n"

    # Rework this. Customization currently gets an App Install label
    for placeholder, content in script_parts.items():
        if content and content.strip():  # Check if content is not None and not empty
            preview_script += f"# {placeholder.replace('_', ' ').title()}\n"
            preview_script += content + "\n\n"

    preview_script += "(...)  # Script footer"

    if "hostname" in distro_data:
        preview_script = preview_script.replace("{hostname}", distro_data["hostname"])

    return preview_script

def build_full_script(template: str, distro_data: Dict[str, Any], output_mode: str) -> str:
    script_parts = {
        "system_upgrade": builder.build_system_upgrade(distro_data, output_mode),
        "system_config": builder.build_system_config(distro_data, output_mode),
        "app_install": builder.build_app_install(distro_data, output_mode),
        "custom_script": builder.build_custom_script(distro_data, output_mode),
    }

    for placeholder, content in script_parts.items():
        template = template.replace(f"{{{{{placeholder}}}}}", content)

    if "hostname" in distro_data:
        template = template.replace("{hostname}", distro_data["hostname"])

    return template

def main():
    # Add a header with a logo and links
    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .header-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 2rem;
        }
        .logo {
            width: 400px;
            height: auto;
            margin-bottom: 1rem;
            animation: fadeIn 1s ease-out;
        }
        .main-header {
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0.5rem;
            animation: fadeIn 1s ease-out 0.3s;
            opacity: 0;
            animation-fill-mode: forwards;
        }
        .sub-header {
            font-size: 1.5em;
            text-align: center;
            font-style: italic;
            margin-bottom: 1rem;
            animation: fadeIn 1s ease-out 0.6s;
            opacity: 0;
            animation-fill-mode: forwards;
        }
    </style>
    <div class="header-container">
        <img src="https://fedoraproject.org/assets/images/fedora-workstation-logo.png" alt="Fedora Logo" class="logo">
        <h1 class="main-header">F-PASS Creator</h1>
        <h2 class="sub-header">Fedora Post-Installation Automated Setup Script</h2>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'script_built' not in st.session_state:
        st.session_state.script_built = False

    template = load_template()
    distro_data, output_mode = render_sidebar()

    script_preview = st.empty()

    updated_script = build_script(distro_data, output_mode)
    script_preview.code(updated_script, language="bash")

    if st.button("Build Your Script"):
        full_script = build_full_script(template, distro_data, output_mode)
        st.session_state.full_script = full_script
        st.session_state.script_built = True

    # Display download button and instructions if script has been built
    if st.session_state.script_built:
        st.download_button(
            label="Download Your Script",
            data=st.session_state.full_script,
            file_name="f-pass.sh",
            mime="text/plain"
        )

        st.markdown("""
        ### Your Script Has Been Created!

        Follow these steps to use your script:

        1. **Download the Script**  
        Click the 'Download Your Script' button above to save the script to your computer.

        2. **Make the Script Executable**  
        There are two methods for doing this:  
        <span style="visibility: hidden;">....</span>A - Right-click on f-pass.sh and select 'Properties'.  
                    <span style="visibility: hidden;">........</span> Gnome: Enable 'Executable as Program' and click 'Ok'.  
                    <span style="visibility: hidden;">........</span> KDE:  Navigate to the 'Permissions' tab, check 'Is executable', and click 'Ok'.  
        <span style="visibility: hidden;">....</span>B - Open a terminal, navigate to the directory containing the downloaded script, and run:
           ```
           chmod +x f-pass.sh
           ```

        3. **Run the Script**  
        In a terminal window, run the script with sudo privileges:
           ```
           sudo ./f-pass.sh
           ```
        """, unsafe_allow_html=True)

    st.markdown(f"""
    ### Impotant Notes:
    <span style="visibility: hidden;">....</span>🛠️ This script may work with other releases, but these commands were written with {distro_data['system_config']['recommended_settings']['apps']['set_hostname']['default']} in mind.  
    <span style="visibility: hidden;">....</span>⚠️  Similarly, this script will install programs and make changes to your system. Use with care.
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
