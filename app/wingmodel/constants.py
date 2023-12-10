import os
import math

## Physical constants

AIR_DENSITY = 1.225 #[kg/m^3]
AIR_KINEMATIC_VISCOSITY = 1.516*1e-5 # [m^/s], at 20 degrees C
G = 9.81 ## [m/s**2]

## Wing model parameters

DELTA_MAX = 0.1 ## maximal relative wing tip displacement
LOAD_FACTOR = 1.0
MIN_SAFETY_FACTOR = 1.5

WARNING_ICON = "⚠️"
FAIL_ICON = "❌"
OK_ICON = "✅"


## Geometry

CHORD_MIN = 50
CHORD_MAX = 1000
CHORD_DEFAULT = 260

SPAN_MIN = 50
SPAN_MAX = 5000
SPAN_DEFAULT = 900

## App settings

STL_MODELS_DIR = os.path.join("app", "static")
CACHE_DIR = os.path.join("app", "cache")

MODEL_COLORS = {
    "box" : "#FFFF00",
    "foam": "#A9A9A9",
    "shell": "#A4D3EE"
}

USE_CACHED_RESULTS = True
CACHE_LIFETIME_SECONDS = 3600*2
DEFAULT_MODEL_CACHE_LIFETIME_SECONDS = 3600*12
