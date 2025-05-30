from CADETProcess.processModel import (
    ComponentSystem, StericMassAction, GeneralRateModel, Inlet, Outlet, FlowSheet, Process
)
from app.models.process import ProcessParams

import numpy as np

def build_process_from_params(params: ProcessParams) -> Process:
    # 1. Component system
    cs = ComponentSystem()
    for name in params.system.components:
        cs.add_component(name)

    # 2. Flow sheet
    units = {}
    for unit in params.flow_sheet.units:
        if unit.unit_type == "Inlet":
            inlet = Inlet(cs, name=unit.name)
            inlet.flow_rate = unit.flow_rate
            units[unit.name] = inlet

        elif unit.unit_type == "Outlet":
            outlet = Outlet(cs, name=unit.name)
            units[unit.name] = outlet

        elif unit.unit_type == "GeneralRateModel":
            binding = unit.binding
            if binding.model_type == "SMA":
                sma = StericMassAction(cs, name="SMA")
                sma.is_kinetic = binding.is_kinetic
                sma.adsorption_rate = binding.adsorption_rate
                sma.desorption_rate = binding.desorption_rate
                sma.characteristic_charge = binding.characteristic_charge
                sma.steric_factor = binding.steric_factor
                sma.capacity = binding.capacity
            else:
                raise ValueError(f"Unsupported binding model: {binding.model_type}")

            column = GeneralRateModel(cs, name=unit.name)
            column.binding_model = sma
            column.length = unit.length
            column.diameter = unit.diameter
            column.bed_porosity = unit.bed_porosity
            column.particle_radius = unit.particle_radius
            column.particle_porosity = unit.particle_porosity
            column.axial_dispersion = unit.axial_dispersion
            column.film_diffusion = column.n_comp * [unit.film_diffusion]
            column.pore_diffusion = unit.pore_diffusion
            column.surface_diffusion = column.n_bound_states * [0.0]

            # Set initial conditions (optional - better as params)
            column.c = [50] + [0] * (column.n_comp - 1)
            column.cp = column.c.copy()
            column.q = [sma.capacity] + [0] * (column.n_bound_states - 1)

            units[unit.name] = column

        else:
            raise ValueError(f"Unsupported unit_type: {unit.unit_type}")

    # 3. Assemble flow sheet
    fs = FlowSheet(cs)
    for unit in units.values():
        fs.add_unit(unit)
    fs.set_product_outlet(units[params.flow_sheet.product_outlet])
    for conn in params.flow_sheet.connections:
        fs.add_connection(units[conn.from_unit], units[conn.to_unit])

    # 4. Build process
    process = Process(fs, name=params.name)
    process.cycle_time = params.cycle_time

    # 5. Events (load/wash/gradient)
    c_load = np.array(params.inlet_concentration)
    c_wash = np.array(params.c_wash)
    c_elute = np.array(params.c_elute)
    gradient_duration = params.cycle_time - params.t_gradient_start
    gradient_slope = (c_elute - c_wash) / gradient_duration
    c_gradient_poly = np.array(list(zip(c_wash, gradient_slope)))

    process.add_event("load", "flow_sheet.inlet.c", c_load)
    process.add_event("wash", "flow_sheet.inlet.c", c_wash, time=params.load_duration)
    process.add_event("grad_start", "flow_sheet.inlet.c", c_gradient_poly, time=params.t_gradient_start)

    return process
