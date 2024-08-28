import json
import logging

distro_data = None
distro_name = None

def set_distro_data(json_data):
    global distro_data
    distro_data = json_data

def get_distro_data():
    global distro_data
    return distro_data

def set_distro_name(selected_distro: str):
    global distro_name
    distro_name = selected_distro

def get_distro_name() -> str:
    global distro_name
    return distro_name