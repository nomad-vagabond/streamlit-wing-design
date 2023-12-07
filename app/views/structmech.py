import json

import streamlit as st
import streamlit.components.v1 as components
from yattag import Doc
import pandas as pd
import numpy as np
import altair as alt

from wingmodel.constants import *


def build_structmech_view(wing_console):
    st.text("")
    _bend_graphs(wing_console)
    _section_preview(wing_console.models_data)
    _static_stats(wing_console)


def _bend_graphs(wing_console):
    span = wing_console.model_props["span"]

    dists = np.linspace(0, span, 100)
    nu_abs = []
    nu_rel = []

    for dist in dists:
        nu = wing_console.get_bend_displacement(dist)
        nu_abs.append(nu)
        nu_rel.append(100*nu/span)

    if nu_rel[-1] > 15:
        color = "#ff9f42"
    elif nu_rel[-1] > 0:
        color = "#37abc8ff"
    else:
        color = "#ef4e4e"

    col1, col2, col3 = st.columns([5,1,6])

    with col1:
        data = pd.DataFrame({"dist": dists, "nu": np.array(nu_rel)})
        chart_nu = (
            alt.Chart(data, title="Relative Bend Deflection")
                .mark_line()
                .encode(
                    x=alt.X('dist', title='Distance from root chord [mm]'),
                    y=alt.Y('nu', title='Δ [%]'), 
                    color=alt.value(color))
                .properties(height=300)
                .configure_title(anchor='middle')
        )

        st.altair_chart(chart_nu, use_container_width=True)
    
    with col3:
        img_path = "./app/img/wing_load_scheme.png"
        st.image(img_path, use_column_width=True, caption="Simplified Wing Load Scheme")


def _static_stats(wing_console):
    model_props = wing_console.model_props

    shell_thickness = model_props["shell_thickness"]
    box_thickness = model_props["box_thickness"]
    profile_height = model_props["profile_height"]
    box_Ixx = model_props["box_Ixx"]
    box_Iyy = model_props["box_Iyy"]

    shell_mass = model_props["shell_mass"]
    foam_mass = model_props["foam_mass"]
    box_mass = model_props["box_mass"]
    console_mass = model_props["total_mass"]
    chord = model_props["chord"]
    span = model_props["span"]
    specific_load = model_props["specific_load"]
    bend_force = model_props["bend_force"]

    bend_stress = float(model_props["bend_stress"])*1e-6
    shear_strss = float(model_props["shear_stress"])*1e-6
    von_mises_stress = float(model_props["von_mises_stress"])*1e-6
    safety = float(model_props["box_tensile_strength"]) / von_mises_stress
    nu_max = wing_console.get_max_bend_displacement()

    col1, col2, col3 = st.columns(3)
    with col1: # geom
        st.text(
            f"Wing tip deflection:\n"
            f"    h = {nu_max:.2f} [mm] \n"
            f"    Δ = {100*nu_max/span:.2f} [%] \n\n"
            f"Chord: {chord:.2f} [mm] \n"
            f"Profile height: {profile_height:.2f} [mm] \n\n"
            f"Shell thickness: {shell_thickness:.2f} [mm] \n"
            f"Box thickness: {box_thickness:.2f} [mm] \n"
            f"Box Ixx: {box_Ixx:.2f} [mm^4] \n"
            # f"Box Iyy: {box_Iyy:.2f} [mm^4] \n"
        )
    with col2: #phys
        st.text(
            f"Total vertical load: {specific_load:.2f} [N/m] \n"
            f"Total bend force: {bend_force:.2f} [N] \n\n"
            f"Console mass: {console_mass:.2f} [kg] \n"
            f"    Shell: {shell_mass:.2f} [kg] \n"
            f"    Foam: {foam_mass:.2f} [kg] \n"
            f"    Box: {box_mass:.2f} [kg]"
        )
    with col3:
        st.text(
            f"Max bend stress: {bend_stress:.2f} [MPa] \n"
            f"Max shear stress: {shear_strss:.2f} [MPa] \n"
            f"Von Mises stress: {von_mises_stress:.2f} [MPa] \n"
            f"Safety factor: {safety:.2f}"
        )



def _section_preview(models_data, alpha=0):
    doc, tag, text, line = ttl = Doc().ttl()

    # Load and embed the JavaScript file
    with open("js/three.min.js", "r") as js_file:
        three_js = js_file.read()

    with open("js/stl-loader.js", "r") as js_file:
        stl_loader = js_file.read()

    with open("js/orbit-controls.js", "r") as js_file:
        orbital_controls = js_file.read()

    with open("js/model-2D-viewer.js", "r") as js_file:
        wing_console_data = [mdata for mdata in models_data if not mdata["part"] == "airfoil"]
        stl_viewer_component = (
            js_file.read()
            .replace('{__MODELS__}', json.dumps(wing_console_data))
            .replace('{__ALPHA__}', "0")
        )

    all_scripts = three_js + "\n" + stl_loader + "\n" + orbital_controls + "\n" + stl_viewer_component

    with tag("div", style="height:250px"):
        with tag('script'):
            doc.asis(all_scripts)
        with tag('stl-viewer'):
            pass

    components.html(doc.getvalue(), height=250)
