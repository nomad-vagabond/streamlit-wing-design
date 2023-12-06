import markdown
import streamlit as st

from wingmodel.constants import *
from .cadmodel import build_model_view
from .aerodynamics import build_aerodynamics_view
from .structmech import build_structmech_view


def build_toolbar(airfoils_data):
    with st.sidebar:
        st.title('Wing Console Generator')
        geom_params = {}

        st.markdown("## Geometry")
        airfoil_repos = sorted(airfoils_data.keys())

        naca_repo_ind = [i for i, repo_name in enumerate(airfoil_repos) if "NACA" in repo_name]
        naca_repo_ind = 0 if not naca_repo_ind else naca_repo_ind[0]

        geom_params["airfoil_group"] = st.selectbox("Airfoil Repository", airfoil_repos, index=naca_repo_ind)
        airfoils = airfoils_data[geom_params["airfoil_group"]]

        airfoil_types = sorted(airfoils.keys())
        airfoil_ind = [i for i, airfoil_name in enumerate(airfoil_types) if "2412" in airfoil_name]
        airfoil_ind = 0 if not airfoil_ind else airfoil_ind[0]

        geom_params["airfoil_type"] = st.selectbox("Airfoil", airfoil_types, index=airfoil_ind)
        geom_params["chord"] = st.slider("Chord", min_value=CHORD_MIN, max_value=CHORD_MAX, value=CHORD_DEFAULT, step=5)
        geom_params["span"] = st.slider("Span", min_value=SPAN_MIN, max_value=SPAN_MAX, value=SPAN_DEFAULT, step=5)
        st.divider()

        st.markdown("## Dynamics")
        dyn_params = {}
        dyn_params["velocity"] = st.number_input(
            "Velocity, [m/s]", min_value=1.0, max_value=100.0, 
            value=35.0, step=1.0
        )
        dyn_params["aoa_type"] = st.selectbox("Airfoil", ["Max Quality", "Max Lift", "Min Drag"])

        st.divider()
        st.markdown("## Material Properties")
        phys_params = {}

        st.markdown("### Box")
        phys_params["box_density"] = st.number_input(
            "Density, [kg/m^3]", min_value=1.0, max_value=20e3, 
            value=1500.0, step=1.0
        )

        col1, col2 = st.columns(2)
        with col1:
            phys_params["box_tensile_strength"] = st.number_input(
                "Tensile strength, [MPa]", min_value=1.0, max_value=100e3, 
                value=450.0, step=1.0
            )
        with col2:
            phys_params["box_tensile_modulus"] = st.number_input(
                "Tensile modulus, [GPa]", min_value=1.0, max_value=1e3, 
                value=35.0, step=1.0
            )

        # st.divider()
        st.markdown("### Foam")
        phys_params["foam_density"] = st.number_input(
            "Density, [kg/m^3]", min_value=1.0, max_value=20e3, 
            value=30.0, step=1.0
        )

        # st.divider()
        st.markdown("### Shell")
        phys_params["shell_density"] = st.number_input(
            "Density, [kg/m^3]", min_value=1.0, max_value=20e3, 
            value=1800.0, step=1.0
        )

        return geom_params, phys_params, dyn_params
        

def build_dashboard(airfoils_data, geom_params, phys_params, dyn_params):
    model_tab, profile_tab, specs_tab, about_tab = st.tabs(
        ["Model Preview", "Aerodynamics", "Structural Mechanics", "About"]
    )

    with model_tab:
        wing_console = build_model_view(airfoils_data, geom_params, phys_params, dyn_params)

    with profile_tab:
        build_aerodynamics_view(wing_console)

    with specs_tab:
        build_structmech_view(wing_console)

    with about_tab:
        with open("README.md") as rf:
            readme = rf.read()
        
        st.markdown(markdown.markdown(readme), unsafe_allow_html=True)
