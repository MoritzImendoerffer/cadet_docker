"""Utility helpers for building CADET Process objects used in tests.

This module isolates the fairly verbose model‑construction code so that
unit tests and integration tests can reuse the exact same reference
process without duplicating hundreds of lines.
"""

from __future__ import annotations

import numpy as np
from CADETProcess.processModel import (
    ComponentSystem,
    StericMassAction,
    Inlet,
    GeneralRateModel,
    Outlet,
    FlowSheet,
    Process,
)

__all__ = ["make_process"]


def make_process() -> Process:
    """Return the canonical test `Process` used by the API test‑suite."""

    cs = ComponentSystem()
    cs.add_component("Salt")
    cs.add_component("A")
    cs.add_component("B")
    cs.add_component("C")

    sma = StericMassAction(cs, name="SMA")
    sma.is_kinetic = True
    sma.adsorption_rate = [0.0, 35.5, 1.59, 7.7]
    sma.desorption_rate = [0.0, 1000, 1000, 1000]
    sma.characteristic_charge = [0.0, 4.7, 5.29, 3.7]
    sma.steric_factor = [0.0, 11.83, 10.6, 10.0]
    sma.capacity = 1200.0

    inlet = Inlet(cs, name="inlet")
    inlet.flow_rate = 6.683738370512285e-8

    column = GeneralRateModel(cs, name="column")
    column.binding_model = sma
    column.length = 0.014
    column.diameter = 0.02
    column.bed_porosity = 0.37
    column.particle_radius = 4.5e-5
    column.particle_porosity = 0.75
    column.axial_dispersion = 5.75e-8
    column.film_diffusion = column.n_comp * [6.9e-6]
    column.pore_diffusion = [7e-10, 6.07e-11, 6.07e-11, 6.07e-11]
    column.surface_diffusion = column.n_bound_states * [0.0]
    column.c = [50, 0, 0, 0]
    column.cp = [50, 0, 0, 0]
    column.q = [sma.capacity, 0, 0, 0]

    outlet = Outlet(cs, name="outlet")

    fs = FlowSheet(cs)
    fs.add_unit(inlet)
    fs.add_unit(column)
    fs.add_unit(outlet, product_outlet=True)
    fs.add_connection(inlet, column)
    fs.add_connection(column, outlet)

    process = Process(fs, name="lwe")
    process.cycle_time = 2000.0
    load_duration = 9.0
    t_gradient_start = 90.0
    gradient_duration = process.cycle_time - t_gradient_start

    c_load = np.array([50.0, 1.0, 1.0, 1.0])
    c_wash = np.array([50.0, 0.0, 0.0, 0.0])
    c_elute = np.array([500.0, 0.0, 0.0, 0.0])
    gradient_slope = (c_elute - c_wash) / gradient_duration
    c_gradient_poly = np.array(list(zip(c_wash, gradient_slope)))

    process.add_event("load", "flow_sheet.inlet.c", c_load)
    process.add_event("wash", "flow_sheet.inlet.c", c_wash, time=load_duration)
    process.add_event(
        "grad_start", "flow_sheet.inlet.c", c_gradient_poly, time=t_gradient_start
    )

    return process
