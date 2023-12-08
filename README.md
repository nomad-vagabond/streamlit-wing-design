# UAV Wing Console Generator

Rectangular Wing Console (v0.1)

Streamlit app based on the [CQ-UAV](https://github.com/nomad-vagabond/cq-uav) library for generation of UAV components with [CadQuery](https://github.com/CadQuery/cadquery) and [SplineCloud](https://splinecloud.com/).

---

![](preview.png)

## Mathematical Model of The Wing Console

### Assumptions
- considered uniform distribution of pressure along the wing span (which is not true in reality);
- UAV pitch angle = 0, meaning horizontal flight mode with arbitrary angle of attack;
- only the wing box section accepts aerodynamic load, which is applied along the central line of the wing box;
- pure box bending is considered;
- wing console is fixed on one of its ends, another end is free;
- wing materials are isotropic;
- the weights of all wing components are considered.

### Geometry

Wing consists of three main parts: three-chamber box compartment (inner body), shell and interim body (XPS foam or other low-density material)

Geometry is automatically reenerated based on the airfoil type and wing size.


## Airfoil data

Airfoil data (profile geometry and aerodynamic coefficients) are collected from the open SplineCloud repositories with the script from the cq-uav library.

Airfoil shapes are approximated with smoothing B-Splines, while sharp tails are thickened to avoid malformed geometry.

## To Run Locally

1. Clone this repository with git

2. Open terminal

3. Install dependencies

    ```
    pip install -r requirements.txt
    ```

4. Run the streamlit app

    ```
    streamlit run app/app.py
    ```

5. A browser window (tab) with the app should appear.

---

Inspired by [obeliskterrain](https://github.com/medicationforall/obeliskterrainapp/tree/main)
