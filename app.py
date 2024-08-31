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
import streamlit as st
from typing import Dict, Any
import session_config
import builder
import logging

# Constants
script_template = 'template.sh'

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

def load_template() -> str:
    with open(script_template, 'r') as file:
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
        session_config.set_distro_name(selected_distro)
    else: #Default to Fedora 40 if nothing has been selected
        distro_file = supported_distros["Fedora 40"]
        session_config.set_distro_name("Fedora 40")

    # Load the distro data
    distro_data = builder.load_app_data(distro_file)

    # Ensure all app entries have a 'selected' key
    distro_data = add_selected_key(distro_data)

    # Store it in the session state
    session_config.set_distro_data(distro_data)

    # output_mode = st.sidebar.radio("Output Mode", ["Quiet", "Verbose"], index=0, help="Select the output mode for the script.")
    output_mode = st.sidebar.selectbox(
        "Selected Terminal Output Mode",
        ["Quiet", "Verbose"],
        help="Determines how much information the terminal will display as the script runs."
    )

    # Generate the sidebar sections for the selected distro
    for options_category, disto_category_keys in distro_data.items():
        if distro_data.items() != "name":
            render_app_section(distro_data, options_category)

    # Advanced section for custom script
    with st.sidebar.expander("Advanced"):
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
        # Iterate over a copy of the dictionary items to avoid modification issues
        subcategories = list(distro_data[options_category].items())

        # Create a list of apps that require special handling
        special_case_apps = [
            "enable_rpmfusion", "set_hostname", "install_multimedia_codecs",
            "install_intel_codecs", "install_amd_codecs", "install_nvidia_codecs",
            "install_virtualbox", "install_microsoft_fonts"
        ]

        for options_subcategory, subcategory_data in subcategories:
            if options_subcategory == "name":
                continue  # Skip 'name' keys

            st.subheader(subcategory_data['name']) # Generate menus for subcategories
            
            for options_app, app_data in subcategory_data['apps'].items():
                if options_app not in special_case_apps:
                    # Create a checkbox for standard options
                    app_selected = st.checkbox(
                        app_data['name'],
                        key=f"{options_category}_{options_subcategory}_{options_app}",
                        help=app_data.get('description', '')
                    )
                    app_data['selected'] = app_selected # Update the selected status in the data

                    if app_selected and 'installation_types' in app_data:
                        installation_type = st.radio(
                            f"Installation type:",
                            list(app_data['installation_types'].keys()),
                            key=f"{options_category}_{options_subcategory}_{options_app}_install_type"
                        )
                        subcategory_data['apps'][options_app]['installation_type'] = installation_type
                else:
                    app_selected = st.checkbox(
                        app_data['name'],
                        key=f"{options_category}_{options_subcategory}_{options_app}",
                        help=app_data.get('description', '')
                    )
                    app_data['selected'] = app_selected
                    
                    if options_category == "system_config":
                        if options_subcategory == "recommended_settings":
                            if options_app == "enable_rpmfusion":
                                distro_data["system_config"]["recommended_settings"][options_app] = app_selected
                            elif options_app == "set_hostname" and app_selected:
                                hostname = st.text_input("Enter the new hostname:")
                                distro_data["system_config"]["recommended_settings"]["hostname"] = hostname
                        elif options_subcategory == "additional_codecs":
                            codec_options = ["install_multimedia_codecs", "install_intel_codecs", "install_amd_codecs", "install_nvidia_codecs"]
                            for codec_option in codec_options:
                                if codec_option in distro_data["system_config"]["additional_codecs"]:
                                    codec_selected = st.checkbox(
                                        distro_data["system_config"]["additional_codecs"][codec_option]['name'],
                                        key=f"system_config_additional_codecs_{codec_option}",
                                        help=distro_data["system_config"]["additional_codecs"][codec_option]['description']
                                    )
                                    distro_data["system_config"]["additional_codecs"][codec_option]['selected'] = codec_selected
                            if any(distro_data["system_config"]["additional_codecs"].get(option, {}).get('selected', False) for option in codec_options):
                                distro_data["system_config"]["recommended_settings"]["enable_rpmfusion"] = True
                                if not app_selected:
                                    st.sidebar.markdown("""
                                        ```
                                        RPM Fusion has been automatically  
                                        added due to codec choices.
                                        ```
                                    """)
                    elif options_category == "management_apps" and options_app == "install_virtualbox" and app_selected:
                        installation_type = st.radio(
                            "Extension Pack",
                            ('with_extension', 'without_extension'),
                            format_func=lambda x: "Download" if x == "with_extension" else "Ignore",
                            key=f"{options_category}_{options_subcategory}_{options_app}_install_type",
                            help="Select if you wish to download the VirtualBox Extension Pack."
                        )
                        subcategory_data['apps'][options_app]['installation_type'] = installation_type
                        if installation_type == 'with_extension':
                            st.warning("⚠️ The extension pack will be saved in your downloads folder. You will still need to manually install it as normal.")
                    elif options_category == "customization" and options_app == "install_microsoft_fonts" and app_selected:
                        installation_type = st.radio(
                            "Windows Fonts Installation Method",
                            ('core', 'windows'),
                            format_func=lambda x: "Core Fonts" if x == "core" else "Windows Fonts",
                            key=f"{options_category}_{options_subcategory}_{options_app}_install_type",
                            help="Choose how to install Windows fonts."
                        )
                        subcategory_data['apps'][options_app]['installation_type'] = installation_type
                        if installation_type == 'windows':
                            st.warning("⚠️ This method requires a valid Windows license. "
                                       "Please ensure you comply with Microsoft's licensing terms.")
                            st.markdown("[Learn more about Windows fonts licensing](https://learn.microsoft.com/en-us/typography/fonts/font-faq)")
                    elif app_selected and 'installation_types' in app_data:
                        installation_type = st.radio(
                            f"Choose {app_data['name']} installation type:",
                            list(app_data['installation_types'].keys()),
                            key=f"{options_category}_{options_subcategory}_{options_app}_install_type"
                        )
                        subcategory_data['apps'][options_app]['installation_type'] = installation_type

                # Special handling for GPG keys
                if options_app == "install_enpass" and app_selected:
                    st.warning("⚠️ During installation, Enpass's YUM repository will automatically be imported.")
                elif options_app == "install_docker_engine" and app_selected:
                    st.warning("⚠️ During installation, Docker's GPG key will automatically be imported.")
                    st.markdown("[You can verify Docker's GPG key here](https://docs.docker.com/engine/install/fedora/)")

    return distro_data

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
    
    preview_script = f"(...)  # Script header\n\n# Selected distro: {session_config.get_distro_name()}\n# Output Mode: {output_mode}\n\n"
    
    # Rework this. Customization currently gets an App Install label
    for placeholder, content in script_parts.items():
        if content and content.strip():  # Check if content is not None and not empty
            preview_script += f"# {placeholder.replace('_', ' ').title()}\n"
            preview_script += content + "\n\n"
    
    preview_script += "(...)  # Script footer"
    
    # Replace the hostname placeholder if it exists
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
    
    # Replace the hostname placeholder if it exists
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
        <span style="visibility: hidden;">....</span>A - Right-click on f-pass.sh and select 'Properties'. Navigate to the 'Permissions' tab, check 'Is executable', and click 'Ok'.  
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
    <span style="visibility: hidden;">....</span>🛠️ This script may work with other releases, but these commands were written with {session_config.get_distro_name()} in mind.  
    <span style="visibility: hidden;">....</span>⚠️  Similarly, this script will install programs and make changes to your system. Use with care.
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
