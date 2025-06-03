import numpy as np
from dotenv import load_dotenv

from CADETProcess.processModel import (
    ComponentSystem, StericMassAction,
    Inlet, GeneralRateModel, Outlet,
    FlowSheet, Process
)
from CADETProcess.simulator import Cadet

solutions = []
for sma_cap in [100, 500, 800, 1000, 1200]:
    cs = ComponentSystem()
    cs.add_component("Salt 1")
    cs.add_component("Salt 2")

    sma = StericMassAction(cs, name="SMA")
    sma.is_kinetic = True
    sma.adsorption_rate = [1.0, 1.0]
    sma.desorption_rate = [1.0, 1.0]
    sma.characteristic_charge = [1.0, 1.0]
    sma.steric_factor = [1.0, 1.0]
    sma.capacity = sma_cap

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
    column.pore_diffusion = [7e-10, 7e-10]
    column.surface_diffusion = [7e-6, 7e-6]
    column.c = [5, 0]
    column.cp = [5, 0]
    column.q = [sma.capacity, 0]

    outlet = Outlet(cs, name="outlet")

    fs = FlowSheet(cs)
    fs.add_unit(inlet)
    fs.add_unit(column)
    fs.add_unit(outlet, product_outlet=True)
    fs.add_connection(inlet, column)
    fs.add_connection(column, outlet)

    process = Process(fs, name="lwe")
    process.cycle_time = 1000.0
    load_duration = 250.0

    c_load = np.array([0.0, 150.0])
    c_wash = np.array([5, 0.0])

    process.add_event("load", "flow_sheet.inlet.c", c_load)
    process.add_event("wash", "flow_sheet.inlet.c", c_wash, time=load_duration)
    #process.add_event("grad_start", "flow_sheet.inlet.c", c_gradient_poly, time=t_gradient_start)

    process_simulator = Cadet()
    simulation_results = process_simulator.simulate(process)
    solutions.append(simulation_results)
    
print("A")
from CADETProcess.plotting import SecondaryAxis
from matplotlib import pyplot as plt

fig, ax = plt.subplots(ncols=1)
for sol in solutions:
    x = sol.solution.column.outlet.time
    y = sol.solution.column.outlet.solution
    ax.plot(x, y)
