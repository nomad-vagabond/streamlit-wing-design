import math
import csv
import json
from dict_hash import sha256

import cadquery as cq
import zipfile
import pandas as pd

from cquav.wing.airfoil import Airfoil
from cquav.wing.profile import AirfoilSection
from cquav.wing.rect_console import  RectangularWingConsole
from cquav.materials import IsotropicMaterial, FluidProperties

from .constants import *


def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]


class WingModelManager:
    """
    Interface for generating wing console CAD model, 
    caching and retreiving model and its properties from cache
    """

    def __init__(self, airfoils_data, geom_params, phys_params, dyn_params, render_type, colors):
        self.airfoils_data = airfoils_data
        self.input_params = {**geom_params, **phys_params, **dyn_params}

        airfoil_group = geom_params["airfoil_group"]
        airfoil_type = geom_params["airfoil_type"]
        self.airfoil = Airfoil(self.airfoils_data[airfoil_group][airfoil_type])

        velocity = dyn_params['velocity']
        self.fluid_props = FluidProperties(AIR_DENSITY, velocity, AIR_KINEMATIC_VISCOSITY)

        hash_keys = [
            geom_params["airfoil_type"], 
            geom_params["chord"], 
            geom_params["span"], 
            geom_params["shell_thickness"],
            str(int(geom_params["lattice"]))
        ]

        self.model_hash = "-".join(map(str, hash_keys))
        self.stl_path = os.path.join(STL_MODELS_DIR, f"wing-console-{self.model_hash}")
        if not os.path.isdir(self.stl_path):
            os.makedirs(self.stl_path)

        if not os.path.isdir(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        self.stl_zip_path = os.path.join(CACHE_DIR, f"wing-console-{self.model_hash}-stl.zip")
        self.step_path = os.path.join(CACHE_DIR, f"wing-console-{self.model_hash}.step")
        self.props_hash = sha256(self.input_params)
        self.props_path = os.path.join(CACHE_DIR, f"wing-console-{self.model_hash}-{self.props_hash}.csv")

        models_data = self.get_cached_stl_models(render_type, colors)
        model_props = self.get_cached_props()
        has_step_model = self.check_cached_step_model()

        if not all([models_data, model_props, has_step_model]) or not USE_CACHED_RESULTS:
            cad_model = self.generate_cad_model(geom_params)
            geom_props = self.eval_geom_props(cad_model)
            static_props = self.eval_static_props(cad_model)
            dynamic_props = self.eval_dynamic_props(cad_model, static_props["total_mass"])
            strength_props = self.eval_strength_props(cad_model, dynamic_props['bend_force'])
            
            models_data = self._cache_stl_models(cad_model, render_type, colors)
            model_props = self._cache_model_props(geom_props, static_props, dynamic_props, strength_props)
            self._cache_stl_zipfile(models_data)
            self._cache_step_model(cad_model)

        self.models_data = models_data
        self.model_props = model_props

    def _cache_model_props(self, geom_props, static_props, dynamic_props, strength_props):
        model_props = {**self.input_params, **geom_props, **static_props, **dynamic_props, **strength_props}
        with open(self.props_path, "w", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=model_props.keys())
            writer.writeheader()
            writer.writerow(model_props)

        return model_props

    def _cache_stl_models(self, cad_model, render_type, colors):
        airfoil_body = cad_model.build_airfoil_body()
        models = [
            { 
                "model": cad_model.foam,
                "name": f"foam__{self.model_hash}",
                "part": "foam",
            },
            { 
                "model": cad_model.front_box, 
                "name": f"box_front__{self.model_hash}", 
                "part": "box",
            },
            { 
                "model": cad_model.central_box,
                "name": f"box_central__{self.model_hash}",
                "part": "box",
            },
            {
                "model": cad_model.rear_box,
                "name": f"box_rear__{self.model_hash}",
                "part": "box",
            },
            {
                "model": cad_model.shell,
                "name": f"shell__{self.model_hash}",
                "part": "shell",
            },
            { 
                "model": airfoil_body,
                "name": f"airfoil__{self.model_hash}",
                "part": "airfoil",
            },
        ]

        models_data = []
        for model in models:
            stl_model_path = os.path.join(self.stl_path, f'{model["name"]}.stl')
            cq.exporters.export(model['model'], stl_model_path, tolerance=1e-4)
            models_data.append(
                {
                    "path": stl_model_path, 
                    "color": colors[model["part"]], 
                    "name": model["name"],
                    "rendr_type": render_type[model["part"]],
                    "part": model["part"],
                }
            )

        return models_data

    def get_cached_stl_models(self, render_type, colors):
        models_data = []

        if os.path.isdir(self.stl_path):
            for part_name in os.listdir(self.stl_path):
                part_type = part_name.split("__")[0].split("_")[0]
                stl_model_path = os.path.join(self.stl_path, part_name)
                models_data.append(
                    {
                        "path": stl_model_path, 
                        "color": colors.get(part_type) or colors['shell'], 
                        "name": part_name.split(".")[0],
                        "rendr_type": render_type.get(part_type, "shaded"),
                        "part": part_type
                    }
                )
        
        return models_data

    def generate_cad_model(self, geom_params):
        chord = self.input_params["chord"]
        span = self.input_params["span"]
        shell_thickness = self.input_params["shell_thickness"]
        lattice = self.input_params["lattice"]
        airfoil_section = AirfoilSection(self.airfoil, chord=chord)
        cad_model = RectangularWingConsole(airfoil_section, length=span,
            min_length=SPAN_MIN, max_length=SPAN_MAX, min_chord=CHORD_MIN, max_chord=CHORD_MAX,
            shell_thickness=shell_thickness, make_lattice=lattice
        )

        return cad_model

    def eval_geom_props(self, cad_model):
        Ixx, Iyy, Izz = cad_model.box_section.inertia_moments

        geom_props = {
            "area": cad_model.length * cad_model.chord * 1e-6, # [m^2]
            "aspect_ratio": cad_model.length / cad_model.chord,
            "shell_thickness": cad_model.shell_thickness,
            "box_thickness": cad_model.box_thickness,
            "profile_height": cad_model.airfoil_section.profile_max_height,
            "box_Ixx": Ixx,
            "box_Iyy": Iyy,
        }

        return geom_props

    def eval_static_props(self, cad_model):
        shell_density = self.input_params["shell_density"]
        foam_density = self.input_params["foam_density"]
        box_density = self.input_params["box_density"]
        box_tensile_strength = self.input_params["box_tensile_strength"]
        box_tensile_modulus = self.input_params["box_tensile_modulus"]
        
        shell_material = IsotropicMaterial(shell_density)
        foam_material = IsotropicMaterial(foam_density)
        box_material = IsotropicMaterial(box_density, box_tensile_strength*1e6, box_tensile_modulus*1e9)

        materials = {
            "box": box_material, 
            "shell": shell_material, 
            "foam": foam_material
        }

        cad_model.assign_materials(materials)

        box_mass = cad_model.get_box_mass()
        foam_mass = cad_model.get_foam_mass()
        shell_mass = cad_model.get_shell_mass()

        total_mass = box_mass + foam_mass + shell_mass

        static_props = {
            "box_mass": box_mass, 
            "foam_mass": foam_mass,
            "shell_mass": shell_mass,
            "total_mass": total_mass,
        }

        return static_props

    def eval_dynamic_props(self, cad_model, total_mass):

        velocity = self.input_params["velocity"]

        reynolds = cad_model.airfoil_section.eval_reynolds(self.fluid_props)

        if self.input_params["aoa_type"] == "Max Quality":
            alpha = self.airfoil.alpha_optimal(reynolds)
        elif self.input_params["aoa_type"] == "Max Lift":
            alpha = self.airfoil.alpha_max_lift(reynolds)
        elif self.input_params["aoa_type"] == "Min Drag":
            alpha = self.airfoil.alpha_min_drag(reynolds)
        
        cl = self.airfoil.eval_cl(alpha, reynolds)
        cd = self.airfoil.eval_cd(alpha, reynolds)
        cm = self.airfoil.eval_cm(alpha, reynolds)

        lift_force, lift_force_arm = cad_model.compute_lift_force(
            alpha, self.fluid_props, load_factor=LOAD_FACTOR, compute_weight_load=False
        )
        center_of_pressure = (0.25*cad_model.chord, lift_force_arm)
        drag_force = cad_model.compute_drag_force(alpha, self.fluid_props)

        bend_force = cad_model.compute_bend_force(alpha, lift_force, drag_force, total_mass)

        console_weight = G * total_mass
        lift_to_weight = lift_force / console_weight

        alpha_rad = alpha * math.pi / 180
        specific_weight = console_weight * math.cos(alpha_rad) * LOAD_FACTOR / (cad_model.length*1e-3)

        cb = cad_model.compute_bend_coefficient(alpha, cl, cd)
        specific_aerodynamic_load = self.fluid_props.dynamic_pressure * cb * (cad_model.chord*1e-3)

        dynamic_props = {
            "alpha": alpha,
            "cl": cl,
            "cd": cd,
            "cm": cm,
            "lift_force": lift_force,
            "drag_force": drag_force,
            "lift_to_weight": lift_to_weight,
            "center_of_pressure": center_of_pressure,
            "velocity": self.fluid_props.velocity,
            "dyn_airpressure": self.fluid_props.dynamic_pressure,
            "specific_load": specific_aerodynamic_load - specific_weight,
            "bend_force": bend_force,
            "reynolds": reynolds
        }

        return dynamic_props

    def eval_strength_props(self, cad_model, bend_force):
        bend_stress = cad_model.get_max_bend_stress(bend_force)
        shear_stress = cad_model.get_max_shear_stress(bend_force)
        von_mises_stress = math.sqrt(bend_stress**2 + 3*shear_stress**2)

        strength_props = {
            'bend_stress': bend_stress,
            'shear_stress': shear_stress,
            'von_mises_stress': von_mises_stress
        }

        return strength_props

    def _cache_step_model(self, cad_model):
        cq_color = lambda part: cq.Color(*hex_to_rgb(MODEL_COLORS[part]), 1)

        assy = cq.Assembly()
        assy.add(cad_model.foam, name="foam", color=cq_color("foam"))
        assy.add(cad_model.front_box, name="left_box", color=cq_color("box"))
        assy.add(cad_model.central_box, name="central_box", color=cq_color("box"))
        assy.add(cad_model.rear_box, name="right_box", color=cq_color("box"))
        assy.add(cad_model.shell, name="shell", color=cq_color("shell"))

        assy.save(self.step_path)

    def _cache_stl_zipfile(self, models_data):
        with zipfile.ZipFile(self.stl_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for model in models_data:
                if model["part"] == "airfoil":
                    continue
                file_path = model["path"]
                zipf.write(file_path, os.path.basename(file_path))

    def check_cached_step_model(self):
        return os.path.isfile(self.step_path)

    def get_cached_props(self):
        if not os.path.isfile(self.props_path):
            return

        df = pd.read_csv(self.props_path)

        return df.to_dict(orient='records')[0]

    def get_max_bend_displacement(self):
        Ixx = self.model_props["box_Ixx"] * (1e-3)**4 # [m^4]
        span = self.model_props["span"] * 1e-3
        load = self.model_props["specific_load"]
        E = self.model_props["box_tensile_modulus"] * 1e9

        nu_max = (load * span**4) / (8 * E * Ixx )
        
        return nu_max * 1e3 ## [mm]

    def get_bend_displacement(self, dist):
        Ixx = self.model_props["box_Ixx"] * (1e-3)**4 # [m^4]
        span = self.model_props["span"] * 1e-3
        load = self.model_props["specific_load"]
        E = self.model_props["box_tensile_modulus"] * 1e9

        d = dist * 1e-3 # [m]
        nu = load * (2*span*d**3 - 3*(span**2)*(d**2) - (d**4)/2) / (12 * E * Ixx)
        
        return -nu * 1e3 ## [mm]
