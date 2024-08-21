# Fedora Workstation NATTD Not Another "Things To Do"!
# Initial System Setup Shell Script Builder for Fedora Workstation
#
# This application is a Streamlit-based web interface that allows users to customize
# and generate a shell script for setting up a fresh Fedora Workstation installation.
# It provides options for system configuration, essential and additional app installation,
# and system customization. The app uses predefined profiles and allows users to select
# individual options or apply preset profiles. It generates a downloadable shell script
# based on the user's selections, which can be run on a Fedora system to automate the
# setup process.
#
# This tool aims to simplify the post-installation process for Fedora users,
# allowing for easy customization and automation of common setup tasks.
#
# Author: Karl Stefan Danisz
# Contact: https://mktr.sbs/linkedin
# Version: 24.08
#
#
# Use responsibly, and always check the script you are about to run.
# This script is licensed under the GNU General Public License v3.0
#
import logging
import streamlit as st
from typing import Dict, Any
import builder

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO in production
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Constants
SCRIPT_TEMPLATE_PATH = 'template.sh'

st.set_page_config(
    page_title="Fedora Things To Do",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/k-mktr/fedora-things-to-do/issues',
        'Report a bug': "https://github.com/k-mktr/fedora-things-to-do/issues",
        'About': """
        #### Not Another "Things To Do"!    
        **Fedora Workstation Setup Script Builder**
        
        A Shell Script Builder for setting up Fedora Workstation after a fresh install.
        
        If you find this tool useful, consider sharing it with others.

        Created by [Karl Stefan Danisz](https://mktr.sbs/linkedin)        
        
        [GitHub Repository](https://github.com/k-mktr/fedora-things-to-do)
        """
    }
)

def load_template() -> str:
    with open(SCRIPT_TEMPLATE_PATH, 'r') as file:
        return file.read()

def render_sidebar() -> Dict[str, Any]:
    # Add centered, clickable logo to the top of the sidebar using HTML
    st.sidebar.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; padding: 10px;">
            <a href="/" target="_self">
                <img src="https://github.com/k-mktr/fedora-things-to-do/blob/master/assets/logo.png?raw=true" width="250" alt="Logo">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.header("Configuration Options")
    options = {"system_config": {}, "essential_apps": {}, "internet_apps": {}, "productivity_apps": {}, "multimedia_apps": {}, "gaming_apps": {}, "management_apps": {}, "customization": {}}

    output_mode = st.sidebar.radio("Output Mode", ["Quiet", "Verbose"], index=0, help="Select the output mode for the script.")

    all_options = builder.generate_options()
    nattd_data = builder.load_nattd()

    logging.debug(f"all_options: {all_options}")
    logging.debug(f"nattd_data['system_config']: {nattd_data['system_config']}")

    # System Configuration section
    with st.sidebar.expander("System Configuration"):
        for option in all_options["system_config"]:
            logging.debug(f"Processing option: {option}")
            logging.debug(f"nattd_data['system_config'][{option}]: {nattd_data['system_config'][option]}")
            
            # Special handling for RPM Fusion
            if option == "enable_rpmfusion":
                rpm_fusion_checkbox = st.checkbox(
                    nattd_data["system_config"][option]["name"],
                    key=f"system_config_{option}",
                    help=nattd_data["system_config"][option]["description"]
                )
                options["system_config"][option] = rpm_fusion_checkbox
            else:
                options["system_config"][option] = st.checkbox(
                    nattd_data["system_config"][option]["name"],
                    key=f"system_config_{option}",
                    help=nattd_data["system_config"][option]["description"]
                )
            
            if option == "set_hostname" and options["system_config"][option]:
                options["hostname"] = st.text_input("Enter the new hostname:")

        # Check if any codec option is selected and update RPM Fusion checkbox
        codec_options = ["install_multimedia_codecs", "install_intel_codecs", "install_amd_codecs"]
        if any(options["system_config"].get(option, False) for option in codec_options):
            options["system_config"]["enable_rpmfusion"] = True
            if not rpm_fusion_checkbox:
                st.sidebar.markdown("**RPM Fusion** has been automatically selected due to codec choices.")

    # Essential Apps section
    with st.sidebar.expander("Essential Applications"):
        essential_apps = nattd_data["essential_apps"]["apps"]
        for app in essential_apps:
            options["essential_apps"][app["name"]] = st.checkbox(
                app["name"],
                key=f"essential_app_{app['name']}",
                help=app["description"]
            )

    # Internet Applications section
    with st.sidebar.expander("Internet Applications"):
        for category, category_data in nattd_data["internet_apps"].items():
            st.subheader(category_data["name"])
            options["internet_apps"][category] = {}
            for app_id, app_info in category_data["apps"].items():
                app_selected = st.checkbox(app_info['name'], key=f"app_{category}_{app_id}", help=app_info['description'])
                options["internet_apps"][category][app_id] = {'selected': app_selected}
                
                if app_selected and 'installation_types' in app_info:
                    installation_type = st.radio(
                        f"Choose {app_info['name']} installation type:",
                        list(app_info['installation_types'].keys()),
                        key=f"{category}_{app_id}_install_type"
                    )
                    options["internet_apps"][category][app_id]['installation_type'] = installation_type

    # Productivity Applications section
    with st.sidebar.expander("Productivity Applications"):
        for category, category_data in nattd_data["productivity_apps"].items():
            st.subheader(category_data["name"])
            options["productivity_apps"][category] = {}
            for app_id, app_info in category_data["apps"].items():
                app_selected = st.checkbox(app_info['name'], key=f"app_{category}_{app_id}", help=app_info['description'])
                options["productivity_apps"][category][app_id] = {'selected': app_selected}
                
                if app_selected and 'installation_types' in app_info:
                    installation_type = st.radio(
                        f"Choose {app_info['name']} installation type:",
                        list(app_info['installation_types'].keys()),
                        key=f"{category}_{app_id}_install_type"
                    )
                    options["productivity_apps"][category][app_id]['installation_type'] = installation_type

    # Multimedia Applications section
    with st.sidebar.expander("Multimedia Applications"):
        for category, category_data in nattd_data["multimedia_apps"].items():
            st.subheader(category_data["name"])
            options["multimedia_apps"][category] = {}
            for app_id, app_info in category_data["apps"].items():
                app_selected = st.checkbox(app_info['name'], key=f"app_{category}_{app_id}", help=app_info['description'])
                options["multimedia_apps"][category][app_id] = {'selected': app_selected}
                
                if app_selected and 'installation_types' in app_info:
                    installation_type = st.radio(
                        f"Choose {app_info['name']} installation type:",
                        list(app_info['installation_types'].keys()),
                        key=f"{category}_{app_id}_install_type"
                    )
                    options["multimedia_apps"][category][app_id]['installation_type'] = installation_type

    # Gaming Applications section
    with st.sidebar.expander("Gaming Applications"):
        for category, category_data in nattd_data["gaming_apps"].items():
            st.subheader(category_data["name"])
            options["gaming_apps"][category] = {}
            for app_id, app_info in category_data["apps"].items():
                app_selected = st.checkbox(app_info['name'], key=f"app_{category}_{app_id}", help=app_info['description'])
                options["gaming_apps"][category][app_id] = {'selected': app_selected}
                
                if app_selected and 'installation_types' in app_info:
                    installation_type = st.radio(
                        f"Choose {app_info['name']} installation type:",
                        list(app_info['installation_types'].keys()),
                        key=f"{category}_{app_id}_install_type"
                    )
                    options["gaming_apps"][category][app_id]['installation_type'] = installation_type

    # Management Applications section
    with st.sidebar.expander("Management Applications"):
        for category, category_data in nattd_data["management_apps"].items():
            st.subheader(category_data["name"])
            options["management_apps"][category] = {}
            for app_id, app_info in category_data["apps"].items():
                app_selected = st.checkbox(app_info['name'], key=f"app_{category}_{app_id}", help=app_info['description'])
                options["management_apps"][category][app_id] = {'selected': app_selected}
                
                if app_selected and 'installation_types' in app_info:
                    installation_type = st.radio(
                        f"Choose {app_info['name']} installation type:",
                        list(app_info['installation_types'].keys()),
                        key=f"{category}_{app_id}_install_type"
                    )
                    options["management_apps"][category][app_id]['installation_type'] = installation_type

    # Customization section
    with st.sidebar.expander("Customization"):
        customization_apps = nattd_data["customization"]["apps"]
        for app_id, app_info in customization_apps.items():
            options["customization"][app_id] = st.checkbox(
                app_info['name'],
                key=f"customization_{app_id}",
                help=app_info['description']
            )
            
            # Special handling for Windows Fonts
            if app_id == "install_microsoft_fonts" and options["customization"][app_id]:
                options["customization"][app_id] = {
                    'selected': True,
                    'installation_type': st.radio(
                        "Windows Fonts Installation Method",
                        ('core', 'windows'),
                        format_func=lambda x: "Core Fonts" if x == "core" else "Windows Fonts",
                        key=f"customization_{app_id}_install_type",
                        help="Choose how to install Windows fonts."
                    )
                }
                
                if options["customization"][app_id]['installation_type'] == 'windows':
                    st.warning("⚠️ This method requires a valid Windows license. "
                               "Please ensure you comply with Microsoft's licensing terms.")
                    st.markdown("[Learn more about Windows fonts licensing](https://learn.microsoft.com/en-us/typography/fonts/font-faq)")

    # Advanced section for custom script
    with st.sidebar.expander("Advanced"):
        st.warning("⚠️ **Caution**: This section is for advanced users. Incorrect shell commands can potentially harm your system. Use with care.")
        
        st.markdown("""
        Guidelines for custom commands:
        - Ensure each command is on a new line
        - Test your commands before adding them here
        - Be aware that these commands will run with sudo privileges
        """)
        
        default_custom_script = 'echo "Created with ❤️ for Open Source"'
        options["custom_script"] = st.text_area(
            "Custom Shell Commands",
            value=default_custom_script,
            help="Enter any additional shell commands you want to run at the end of the script.",
            height=200,
            key="custom_script_input"
        )
        
        if options["custom_script"].strip() != default_custom_script:
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
    <div class="link-bar">
        <a href="https://fedoraproject.org/workstation/" target="_blank" style="text-decoration: none;" aria-label="Fedora Workstation">Still on the fence?<br>Grab your Fedora now!</a>
    </div>
    <div class="separator"></div>
    <div style="text-align: center; padding: 55px 0;">
        <p style="margin-bottom: 5px;">Created with ❤️ for Open Source</p>
        <a href="https://mktr.sbs/linkedin" target="_blank" style="text-decoration: none; color: #8da9c4;" aria-label="Karol Stefan Danisz LinkedIn">
            <i>by Karol Stefan Danisz</i>
        </a>
    </div>
    """, unsafe_allow_html=True)

    return options, output_mode


def build_script(options: Dict[str, Any], output_mode: str) -> str:
    script_parts = {
        "system_upgrade": builder.build_system_upgrade(options, output_mode),
        "system_config": builder.build_system_config(options, output_mode),
        "app_install": builder.build_app_install(options, output_mode),
        "customization": builder.build_customization(options, output_mode),
        "custom_script": builder.build_custom_script(options, output_mode),
    }
    
    preview_script = "(...)  # Script header and initial setup\n\n"
    
    for placeholder, content in script_parts.items():
        if content and content.strip():  # Check if content is not None and not empty
            preview_script += f"# {placeholder.replace('_', ' ').title()}\n"
            preview_script += content + "\n\n"
    
    preview_script += "(...)  # Script footer"
    
    # Replace the hostname placeholder if it exists
    if "hostname" in options:
        preview_script = preview_script.replace("{hostname}", options["hostname"])
    
    return preview_script

def build_full_script(template: str, options: Dict[str, Any], output_mode: str) -> str:
    script_parts = {
        "system_upgrade": builder.build_system_upgrade(options, output_mode),
        "system_config": builder.build_system_config(options, output_mode),
        "app_install": builder.build_app_install(options, output_mode),
        "customization": builder.build_customization(options, output_mode),
        "custom_script": builder.build_custom_script(options, output_mode),
    }
    
    for placeholder, content in script_parts.items():
        template = template.replace(f"{{{{{placeholder}}}}}", content)
    
    # Replace the hostname placeholder if it exists
    if "hostname" in options:
        template = template.replace("{hostname}", options["hostname"])
    
    return template

def main():
    logging.info("Starting main function")
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
        <h1 class="main-header">Not Another <i>'Things To Do'!</i></h1>
        <h2 class="sub-header">Fedora Workstation Initial System Setup Shell Script Builder</h2>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'script_built' not in st.session_state:
        st.session_state.script_built = False

    logging.info("Loading template")
    template = load_template()
    logging.info("Rendering sidebar")
    options, output_mode = render_sidebar()

    logging.info("Creating script preview")
    script_preview = st.empty()

    logging.info("Building script")
    updated_script = build_script(options, output_mode)
    logging.info("Displaying script preview")
    script_preview.code(updated_script, language="bash")

    if st.button("Build Your Script"):
        logging.info("Building full script")
        full_script = build_full_script(template, options, output_mode)
        st.session_state.full_script = full_script
        st.session_state.script_built = True

    # Display download button and instructions if script has been built
    if st.session_state.script_built:
        st.download_button(
            label="Download Your Script",
            data=st.session_state.full_script,
            file_name="fedora_things_to_do.sh",
            mime="text/plain"
        )
        
        st.markdown("""
        ### Your Script Has Been Created!

        Follow these steps to use your script:

        1. **Download the Script**: Click the 'Download Your Script' button above to save the script to your computer.

        2. **Make the Script Executable**: Open a terminal, navigate to the directory containing the downloaded script, and run:
           ```
           chmod +x fedora_things_to_do.sh
           ```

        3. **Run the Script**: Execute the script with sudo privileges:
           ```
           sudo ./fedora_things_to_do.sh
           ```

        ⚠️ **Caution**: This script will make changes to your system. Please review the script contents before running and ensure you understand the modifications it will make.
        """)

    logging.info("Main function completed")

if __name__ == "__main__":
    main()
