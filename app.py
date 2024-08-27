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

# Constants
script_template = 'template.sh'

st.set_page_config(
    page_title="Fedora Things To Do",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "https://github.com/papercutter0324/F-PASS/issues",
        'About': """
        #### F-PASS   
        **Fedora Post-Installation Automated Setup Script**
        
        A shell script generating tool for automating the final steps of setting up
        a fresh Fedora Workstation installion.
        
        If you find this tool useful, feel free to share, suggest improvements, and
        propose changes.

        Created by papercutter0324
        [GitHub Repository](https://github.com/papercutter0324/F-PASS)
        """
    }
)

def load_template() -> str:
    with open(script_template, 'r') as file:
        return file.read()

def render_sidebar() -> Dict[str, Any]:
    # Add centered, clickable logo to the top of the sidebar using HTML
    st.sidebar.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; padding: 10px;">
            <a href="/" target="_self">
                <img src="https://github.com/papercutter0324/F-PASS/blob/master/assets/logo.png?raw=true" width="240" alt="Logo">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.header("Configuration Options")
    options = {"system_config": {}, "essential_apps": {}, "internet_apps": {}, "productivity_apps": {}, "multimedia_apps": {}, "gaming_apps": {}, "management_apps": {}, "customization": {}}
    supported_distros = {"Fedora 40": 'fedora_data.json'}

    selected_distro = st.sidebar.selectbox("Choose a Distribution", list(supported_distros.keys()), help="Load the options supported for your distro.")

    if selected_distro: # Figure out how to denote selected distro in the build window.
        distro_file = supported_distros[selected_distro]
    else: #Default to Fedora 40 if nothing has been selected
        distro_file = supported_distros["Fedora 40"]

    # Load the distro data and store it in the session state
    distro_data = builder.load_app_data(distro_file)
    session_config.set_distro_data(distro_data)

    # output_mode = st.sidebar.radio("Output Mode", ["Quiet", "Verbose"], index=0, help="Select the output mode for the script.")
    output_mode = st.sidebar.selectbox(
        "Selected Terminal Output Mode",
        ["Quiet", "Verbose"],
        help="Determines how much information the terminal will display as the script runs."
    )

    # Generate the sidebar and valid options based on the loaded data set
    all_options = builder.generate_options()

    # System Configuration section
    with st.sidebar.expander("System Configuration"):
        for option in all_options["system_config"]:
            # Special handling for RPM Fusion
            if option == "enable_rpmfusion":
                rpm_fusion_checkbox = st.checkbox(
                    distro_data["system_config"][option]["name"],
                    key=f"system_config_{option}",
                    help=distro_data["system_config"][option]["description"]
                )
                options["system_config"][option] = rpm_fusion_checkbox
            else:
                options["system_config"][option] = st.checkbox(
                    distro_data["system_config"][option]["name"],
                    key=f"system_config_{option}",
                    help=distro_data["system_config"][option]["description"]
                )
            
            if option == "set_hostname" and options["system_config"][option]:
                options["hostname"] = st.text_input("Enter the new hostname:")

        # Check if any codec option is selected and update RPM Fusion checkbox
        codec_options = ["install_multimedia_codecs", "install_intel_codecs", "install_amd_codecs", "install_nvidia_codecs"]
        if any(options["system_config"].get(option, False) for option in codec_options):
            options["system_config"]["enable_rpmfusion"] = True
            if not rpm_fusion_checkbox:
                st.sidebar.markdown("**RPM Fusion** has been automatically selected due to codec choices.")

    # Essential Apps section
    with st.sidebar.expander("Essential Applications"):
        essential_apps = distro_data["essential_apps"]["apps"]
        for app in essential_apps:
            options["essential_apps"][app["name"]] = st.checkbox(
                app["name"],
                key=f"essential_app_{app['name']}",
                help=app["description"]
            )

    options = render_app_section("internet_apps", "Internet", distro_data, options)
    options = render_app_section("productivity_apps", "Productivity", distro_data, options)
    options = render_app_section("multimedia_apps", "Multimedia", distro_data, options)
    options = render_app_section("gaming_apps", "Gaming", distro_data, options)
    options = render_app_section("management_apps", "Management", distro_data, options)
    options = render_app_section("customization", "Customization", distro_data, options)

    # Advanced section for custom script
    with st.sidebar.expander("Advanced"):
        st.warning("""⚠️ **Caution**: Intended for advanced users. Incorrect shell commands can potentially harm your system or render it inoperable.
                   \nUse with care!""")
        
        default_custom_text = '# Each command goes on a new line.'
        options["custom_script"] = st.text_area(
            "Custom Commands:",
            value=default_custom_text,
            help="Enter any additional shell commands you want to run at the end of the script.",
            height=200,
            key="custom_script_input"
        )
        
        if options["custom_script"].strip() != default_custom_text:
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

    return options, output_mode

def render_app_section(app_category_key: str, app_category_name: str, distro_data: str, options: Dict[str, Any]) -> Dict[str, Any]:
    with st.sidebar.expander(f"{app_category_name} Applications"):
        for category, category_data in distro_data[app_category_key].items():
            st.subheader(category_data["name"])
            options[app_category_key][category] = {}
            
            for app_id, app_info in category_data["apps"].items():
                app_selected = st.checkbox(app_info['name'], key=f"app_{category}_{app_id}", help=app_info['description'])
                options[app_category_key][category][app_id] = {'selected': app_selected}
                
                # Handling for special cases
                if app_id == "install_virtualbox" and options["management_apps"][category][app_id]['selected'] == True:
                    options[app_category_key][category][app_id] = {
                        'selected': True,
                        'installation_type': st.radio(
                            "Extension Pack",
                            ('with_extension', 'without_extension'),
                            format_func=lambda x: "Download" if x == "with_extension" else "Ignore",
                            key=f"app_{category}_{app_id}_install_type",
                            help="Selected if you wish to download the VirtualBox Extension Pack."
                        )
                    }

                    # Inform user of download destination
                    if options["management_apps"][category][app_id]['installation_type'] == 'with_extension':
                        st.warning("⚠️ The extension pack will be save in your downloads folder. You will still need to manually install it as normal.")
                elif app_id == "install_microsoft_fonts" and options["customization"][category][app_id]['selected'] == True:
                    options["customization"][category][app_id] = {
                        'selected': True,
                        'installation_type': st.radio(
                            "Windows Fonts Installation Method",
                            ('core', 'windows'),
                            format_func=lambda x: "Core Fonts" if x == "core" else "Windows Fonts",
                            key=f"customization_{app_id}_install_type",
                            help="Choose how to install Windows fonts."
                        )
                    }
                    
                    if options["customization"][category][app_id]['installation_type'] == 'windows':
                        st.warning("⚠️ This method requires a valid Windows license. "
                                "Please ensure you comply with Microsoft's licensing terms.")
                        st.markdown("[Learn more about Windows fonts licensing](https://learn.microsoft.com/en-us/typography/fonts/font-faq)")
                
                elif app_selected and 'installation_types' in app_info:
                    installation_type = st.radio(
                        f"Choose {app_info['name']} installation type:",
                        list(app_info['installation_types'].keys()),
                        key=f"{category}_{app_id}_install_type"
                    )
                    options[app_category_key][category][app_id]['installation_type'] = installation_type
                
                # Special handling for when GPG keys need to be imported
                if app_id == "install_enpass" and options["management_apps"][category][app_id]['selected'] == True:
                    st.warning("⚠️ During installation, Enpass's YUM repository will automatically be imported.")
                elif app_id == "install_docker_engine" and options["management_apps"][category][app_id]['selected'] == True:
                    st.warning("⚠️ During installation, Enpass's GPG key will automatically be imported.")
                    st.markdown("[You can verify Docker's GPG key here](https://docs.docker.com/engine/install/fedora/)")
                    
    return options

def build_script(options: Dict[str, Any], output_mode: str) -> str:
    script_parts = {
        "system_upgrade": builder.build_system_upgrade(options, output_mode),
        "system_config": builder.build_system_config(options, output_mode),
        "app_install": builder.build_app_install(options, output_mode),
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
        "custom_script": builder.build_custom_script(options, output_mode),
    }
    
    for placeholder, content in script_parts.items():
        template = template.replace(f"{{{{{placeholder}}}}}", content)
    
    # Replace the hostname placeholder if it exists
    if "hostname" in options:
        template = template.replace("{hostname}", options["hostname"])
    
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
        <h1 class="main-header">F-PASS</h1>
        <h2 class="sub-header">Fedora Post-Installation Automated Setup Script</h2>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'script_built' not in st.session_state:
        st.session_state.script_built = False

    template = load_template()
    options, output_mode = render_sidebar()

    script_preview = st.empty()

    updated_script = build_script(options, output_mode)
    script_preview.code(updated_script, language="bash")

    if st.button("Build Your Script"):
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

if __name__ == "__main__":
    main()
