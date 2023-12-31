import os, time, json, sys, re, shutil
from uuid import uuid4
import glob
import time
from datetime import datetime, date
from pathlib import Path
import pkg_resources

import streamlit as st

from views import build_toolbar, build_dashboard
from wingmodel.constants import *


sys.stdout.flush()

default_model_name_pattern = re.compile(f"(?=.*2412.*{CHORD_DEFAULT}-{SPAN_DEFAULT}-1-0)")


def _initialize_session():
    if 'models' not in st.session_state:
        st.session_state['models'] = []

    if "session_id" not in st.session_state:
        st.session_state['session_id'] = uuid4()


def _clean_cache():
    now = time.time()
    for filename in os.listdir(CACHE_DIR):
        filepath = os.path.join(CACHE_DIR, filename)
        filestamp = os.stat(filepath).st_mtime

        if default_model_name_pattern.search(filename):
            threshold = now - DEFAULT_MODEL_CACHE_LIFETIME_SECONDS
        else:
            threshold = now - CACHE_LIFETIME_SECONDS
        
        if filestamp < threshold:
            os.remove(filepath)
            print(f"Removed cached file {filename}")


def _clean_stl_models():
    now = time.time()
    for dirname in os.listdir(STL_MODELS_DIR):
        dir_path = os.path.join(STL_MODELS_DIR, dirname)

        if not os.path.isdir(dir_path):
            continue

        dirstamp = os.stat(dir_path).st_mtime

        if default_model_name_pattern.search(dirname):
            threshold = now - DEFAULT_MODEL_CACHE_LIFETIME_SECONDS
        else:
            threshold = now - CACHE_LIFETIME_SECONDS

        if dirstamp < threshold:
            shutil.rmtree(dir_path)
            print(f"Removed stl models directory {dirname}")


if __name__ == "__main__":
    st.set_page_config(page_title="Wing Console Generator", page_icon="✈️", layout="wide")
    _initialize_session()
    
    airfoils_collection = pkg_resources.resource_filename('cquav', 'wing/airfoil/airfoils_collection.json')
    with open(airfoils_collection) as ac:
        airfoils_data = json.loads(ac.read())

    geom_params, phys_params, dyn_params = build_toolbar(airfoils_data)
    build_dashboard(airfoils_data, geom_params, phys_params, dyn_params)
    
    _clean_stl_models()
    _clean_cache()
