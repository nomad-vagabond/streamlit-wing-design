import os, time, json
from uuid import uuid4
import glob
import time
from datetime import datetime, date
from pathlib import Path
import pkg_resources

import streamlit as st

from views import build_toolbar, build_dashboard
from wingmodel.constants import CACHE_DIR, CACHE_LIFETIME_SECONDS


def _initialize_session():
    if 'models' not in st.session_state:
        st.session_state['models'] = []

    if "session_id" not in st.session_state:
        st.session_state['session_id'] = uuid4()


def _clean_cahe():
    now = time.time()
    for filename in os.listdir(CACHE_DIR):
        filestamp = os.stat(os.path.join(CACHE_DIR, filename)).st_mtime
        threshold = now - CACHE_LIFETIME_SECONDS
        if filestamp < threshold:
            print(filename)


def __clean_up_static_files():
    files = glob.glob("app/static/*.stl")
    today = datetime.today()
    for file_name in files:
        file_path = Path(file_name)
        modified = file_path.stat().st_mtime
        modified_date = datetime.fromtimestamp(modified)
        delta = today - modified_date
        #print('total seconds '+str(delta.total_seconds()))
        if delta.total_seconds() > 1200: # 20 minutes
            #print('removing '+file_name)
            file_path.unlink()


if __name__ == "__main__":
    st.set_page_config(page_title="Wing Console Generator", page_icon="✈️", layout="wide")
    _initialize_session()
    
    airfoils_collection = pkg_resources.resource_filename('cquav', 'wing/airfoil/airfoils_collection.json')
    with open(airfoils_collection) as ac:
        airfoils_data = json.loads(ac.read())

    geom_params, phys_params, dyn_params = build_toolbar(airfoils_data)
    build_dashboard(airfoils_data, geom_params, phys_params, dyn_params)

    # __clean_up_static_files()
    # _clean_cahe()