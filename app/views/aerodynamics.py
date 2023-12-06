import json

import streamlit as st
import streamlit.components.v1 as components
from yattag import Doc
import pandas as pd
import numpy as np
import altair as alt

from wingmodel.constants import *


def build_aerodynamics_view(wing_console):
    st.text("")
    alpha = wing_console.model_props["alpha"]
    _profile_graphs(wing_console)
    _profile_preview(wing_console.models_data, alpha)
    _profile_stats(wing_console)


def _profile_graphs(wing_console):
    airfoil = wing_console.airfoil

    alpha_const = float(wing_console.model_props["alpha"])
    reynolds = float(wing_console.model_props["reynolds"])
    cl_const = float(airfoil.eval_cl(alpha_const, reynolds))
    cd_const = float(airfoil.eval_cd(alpha_const, reynolds))
    cl_to_cd_const = cl_const/cd_const

    alpha_vals = []
    cl_vals = []
    cd_vals = []
    cl_to_cd_vals = []

    for alpha in np.linspace(-20, 20, 161):
        cl = airfoil.eval_cl(alpha, reynolds)
        cd = airfoil.eval_cd(alpha, reynolds)
        if not all([np.isnan(cl), np.isnan(cd)]):
            alpha_vals.append(alpha)
            cl_vals.append(float(cl))
            cd_vals.append(float(cd))
            cl_to_cd_vals.append(float(cl)/float(cd))

    col1, col2, col3 = st.columns(3)
    with col1:
        data = pd.DataFrame({"alpha": alpha_vals, "Cl": cl_vals})
        point = pd.DataFrame({"alpha": [alpha_const], "Cl": [cl_const]})

        chart_cl_line = (alt.Chart(data).mark_line().encode(x='alpha', y='Cl', color=alt.value("#04BA71")))
        chart_cl_point = (alt.Chart(point).mark_point().encode(x='alpha', y='Cl', color=alt.value("#04BA71")))
        
        chart_cl = (alt.layer(chart_cl_line, chart_cl_point)
                       .properties(height=280, title="Lift Coefficient")
                       .configure_title(anchor='middle')
                    )

        st.altair_chart(chart_cl, use_container_width=True)

    with col2:
        data = pd.DataFrame({"alpha": alpha_vals, "Cd": cd_vals})
        point = pd.DataFrame({"alpha": [alpha_const], "Cd": [cd_const]})

        chart_cd_line = (alt.Chart(data).mark_line().encode(x='alpha', y='Cd', color=alt.value("#FFAA00")))
        chart_cd_point = (alt.Chart(point).mark_point().encode(x='alpha', y='Cd', color=alt.value("#FFAA00")))

        chart_cd = (alt.layer(chart_cd_line, chart_cd_point)
                       .properties(height=280, title="Drag Coefficient")
                       .configure_title(anchor='middle')
                    )

        st.altair_chart(chart_cd, use_container_width=True)

    with col3:
        data = pd.DataFrame({"alpha": alpha_vals, "Cl/Cd": cl_to_cd_vals})
        point = pd.DataFrame({"alpha": [alpha_const], "Cl/Cd": [cl_to_cd_const]})

        chart_cl_to_cd_line = (alt.Chart(data).mark_line().encode(x='alpha', y='Cl/Cd', color=alt.value("#1B96C6")))
        chart_cl_to_cd_point = (alt.Chart(point).mark_point().encode(x='alpha', y='Cl/Cd', color=alt.value("#1B96C6")))

        chart_cl_to_cd = (alt.layer(chart_cl_to_cd_line, chart_cl_to_cd_point)
                       .properties(height=280, title="Quality")
                       .configure_title(anchor='middle')
                    )

        st.altair_chart(chart_cl_to_cd, use_container_width=True)


def _profile_preview(models_data, alpha=0):
    doc, tag, text, line = ttl = Doc().ttl()

    # Load and embed the JavaScript file
    with open("js/three.min.js", "r") as js_file:
        three_js = js_file.read()

    with open("js/stl-loader.js", "r") as js_file:
        stl_loader = js_file.read()

    with open("js/orbit-controls.js", "r") as js_file:
        orbital_controls = js_file.read()

    with open("js/model-2D-viewer.js", "r") as js_file:
        airfoil_data  = [m for m in models_data if m["part"] == "airfoil"]
        stl_viewer_component = (
            js_file.read()
            .replace('{__MODELS__}', json.dumps(airfoil_data))
            .replace('{__ALPHA__}', str(float(alpha)))
        )

    all_scripts = three_js + "\n" + stl_loader + "\n" + orbital_controls + "\n" + stl_viewer_component

    with tag("div", style="height:280px"):
        with tag('script'):
            doc.asis(all_scripts)
        with tag('stl-viewer'):
            pass

    components.html(doc.getvalue(), height=280)


def _profile_stats(wing_console):
    model_props = wing_console.model_props
    console_weight = G * model_props["total_mass"]
    
    lift = model_props["lift_force"]
    drag = model_props["drag_force"]
    alpha = model_props["alpha"]
    cl = model_props["cl"]
    cd = model_props["cd"]
    cm = model_props["cm"]
    cl_to_cd = cl/cd
    area = model_props["area"]
    reynolds = model_props["reynolds"]

    col1, col2 = st.columns([4, 8])
    with col1:
        st.text(
            f"Angle of Attack: {alpha:.2f} [°] \n"
            f"Lift force: {lift:.2f} [N] \n"
            f"Drag force: {drag:.2f} [N] \n"
            f"Area: {area:.2f} [m^2] \n"
            
        )
    with col2:
        st.text(
            f"Cl: {cl:.4f} \t"
            f"Cd: {cd:.4f} \t"
            f"Cm: {cm:.4f} \t"
            f"Cl/Cd: {cl_to_cd:.4f} \n\n"
            f"Reynolds Number: {reynolds:.4e} (at 0 altitude and 20°C)"
        )
