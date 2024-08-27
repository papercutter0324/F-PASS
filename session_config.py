import json
import logging

distro_data = None

def set_distro_data(json_data):
    global distro_data
    distro_data = json_data

def get_distro_data():
    global distro_data
    return distro_data