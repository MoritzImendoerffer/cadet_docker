from __future__ import annotations
from typing import Dict
import numpy as np

from CADETProcess.processModel import (
    ComponentSystem, Inlet, Outlet, FlowSheet, Process,
)

from rate_model_registry import rate_models
from binding_model_registry import binding_models

from .models import SimulationPayload

__all__ = ["build_process"]


def _np(seq):
    """Convert any sequence to a NumPy array of `float64`."""
    return np.asarray(seq, dtype=float)


def build_process(payload: SimulationPayload) -> Process:

    cs = ComponentSystem()
    for comp in payload.ComponentSystemParams.components:
        cs.add_component(comp)

    bp = payload.BindingParams
    # inititae the binding class
    binding_cls = binding_models.get(bp.name)
    binding = binding_cls(cs, name=bp.name)
    binding.parameters = {k: bp.parameters[k] for k in binding.required_parameters}


    rmp = payload.RateModelParams
    rate_cls = rate_models.get[rmp.name]
    column = rate_cls(cs, name="column")
    column.parameters = {k: rmp.parameters[k] for k in column.required_parameters}
    column.surface_diffusion = list(rmp.surface_diffusion)
    column.binding_model = binding

    # initialise column states (c, cp, q) with equilibration values
    column.c = list(payload.ProcessParams.equilibration_conc)
    column.cp = column.c.copy()
    column.q = [binding.capacity] + [0.0] * (len(column.q) - 1) # assumes no other component is bound

    inlet = Inlet(cs, name="inlet")
    outlet = Outlet(cs, name="outlet")

    fs = FlowSheet(cs)
    fs.add_unit(inlet)
    fs.add_unit(column)
    fs.add_unit(outlet, product_outlet=True)
    fs.add_connection(inlet, column)
    fs.add_connection(column, outlet)

    pp = payload.ProcessParams
    process = Process(fs, name=pp.name)
    process.cycle_time = pp.cycle_time

    c_equi   = _np(pp.equilibration_conc)
    c_load   = _np(pp.load_conc)
    c_wash   = _np(pp.wash_conc)
    c_elute  = _np(pp.elute_conc)

    # Gradient poly starts at wash concentration and ramps linearly to elution
    grad_duration = pp.cycle_time - pp.gradient_start
    gradient_slope = (c_elute - c_wash) / grad_duration
    c_gradient_poly = np.vstack((c_wash, gradient_slope)).T  # shape (n_comp, 2)

    # Add events -------------------------------------------------------
    process.add_event("equi",  "flow_sheet.inlet.c", c_equi,   time=pp.equilibration_start)
    process.add_event("load",  "flow_sheet.inlet.c", c_load,   time=pp.load_start)
    process.add_event("wash",  "flow_sheet.inlet.c", c_wash,   time=pp.wash_start)
    process.add_event("grad",  "flow_sheet.inlet.c", c_gradient_poly, time=pp.gradient_start)

    return process
