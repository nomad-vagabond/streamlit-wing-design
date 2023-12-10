import os
import time
import json

import streamlit as st
import streamlit.components.v1 as components
import cadquery as cq
from yattag import Doc

from wingmodel.constants import *
from wingmodel import WingModelManager


def build_model_view(airfoils_data, geom_params, phys_params, dyn_params):
    render_type, colors = _model_display_options()

    start = time.time()
    with st.spinner('Generating Model..'):
        wing_console = WingModelManager(airfoils_data, geom_params, phys_params, dyn_params, render_type, colors)
        model_props = wing_console.model_props
        end = time.time()

        console_mass = model_props["total_mass"]
        shell_rel_mass = 100 * model_props["shell_mass"] / console_mass
        foam_rel_mass = 100 * model_props["foam_mass"] / console_mass
        box_rel_mass = 100 * model_props["box_mass"] / console_mass
        area = model_props["area"]
        aspect_ratio = model_props["aspect_ratio"]
        alpha = model_props["alpha"]
        lift = model_props["lift_force"]
        lift_to_weight = model_props["lift_to_weight"]

        ltw_icon = FAIL_ICON if lift_to_weight<=1 else OK_ICON

        _models_preview(wing_console.models_data)
        col1, col2 = st.columns([8,4])

        with col1:
            st.text(
                f"Aspect ratio: {aspect_ratio:.2f} \n"
                f"Excess lift force: {lift:.2f} [N] \n"
                f"Console mass: {console_mass:.2f} [kg] \n"
                f"    shell: {shell_rel_mass:.2f}%, frame: {foam_rel_mass:.2f}%, box: {box_rel_mass:.2f}% \n"
                f"{ltw_icon} Lift to weight ratio: {lift_to_weight:.2f}"
            )
            st.button(label=f"Download Full Data")

        with col2:
            with open(wing_console.step_path, "rb") as file:
                st.download_button(
                    label=f"Download STEP Model",
                    data=file,
                    file_name=f'{wing_console.model_hash}.step',
                    mime=f"model/step"
                )

            with open(wing_console.stl_zip_path, "rb") as file:
                st.download_button(
                    label=f"Download STL Models",
                    data=file,
                    file_name=f'{wing_console.model_hash}-stl.zip',
                    mime="application/zip"
                )
            
    return wing_console


def _model_display_options():
    render_type = {}
    colors = {}
    options = ["shaded", "transparent", "wireframe", "hidden"]
    display = {
        "shaded": "🌔  shaded",
        "transparent": "⚪  transparent",
        "wireframe": "🌐  wireframe",
        "hidden": "🚫  hidden"
    }

    model_col, shell_col, foam_col, box_col = st.columns(4)

    with model_col:
        generate_button = st.button('🗘 Reload', use_container_width=False)
    
    with shell_col:
        col1, col2 = st.columns([2,8])
        with col2:
            st.markdown("Shell")
        with col1:
            colors["shell"] = st.color_picker('Shell Color', MODEL_COLORS['shell'], label_visibility="collapsed")
            colors["airfoil"] = colors["shell"]
        render_type["shell"] = st.selectbox("Shell Display", options, 
        index=0, format_func=lambda v: display[v], label_visibility="collapsed")
        render_type["airfoil"] = render_type["shell"]

    with foam_col:
        col1, col2 = st.columns([2,8])
        with col2:
            st.markdown("Frame")
        with col1:
            colors["foam"] = st.color_picker('Foam Color', MODEL_COLORS['foam'], label_visibility="collapsed")
        render_type["foam"] = st.selectbox("Foam Display", options, 
            index=0, format_func=lambda v: display[v], label_visibility="collapsed")

    with box_col:
        col1, col2 = st.columns([2,8])
        with col2:
            st.markdown("Box")
        with col1:
            colors["box"] = st.color_picker('Box Color', MODEL_COLORS['box'], label_visibility="collapsed")
        render_type["box"] = st.selectbox("Box Display", options, 
            index=0, format_func=lambda v: display[v], label_visibility="collapsed")
    
    return render_type, colors


def _models_preview(models_data):
    doc, tag, text, line = ttl = Doc().ttl()

    # Load and embed the JavaScript file
    with open("js/three.min.js", "r") as js_file:
        three_js = js_file.read()

    with open("js/stl-loader.js", "r") as js_file:
        stl_loader = js_file.read()

    with open("js/orbit-controls.js", "r") as js_file:
        orbital_controls = js_file.read()

    with open("js/model-3D-viewer.js", "r") as js_file:
        wing_console_data = [mdata for mdata in models_data if not mdata["part"] == "airfoil"]
        stl_viewer_component = (
            js_file.read().replace('{__MODELS__}', json.dumps(wing_console_data))
        )

    all_scripts = three_js + "\n" + stl_loader + "\n" + orbital_controls + "\n" + stl_viewer_component

    with tag("div", style="height:500px;"):
        with tag('script'):
            doc.asis(all_scripts)
        line("stl-viewer", "")

    components.html(doc.getvalue(), height=500)

    
