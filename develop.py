import os
import dill
import base64
import hmac
import hashlib
import requests
import numpy as np
from dotenv import load_dotenv
import json
from CADETProcess.processModel import (
    ComponentSystem, StericMassAction,
    Inlet, GeneralRateModel, Outlet,
    FlowSheet, Process
)
from CADETProcess.simulator import Cadet

# Load shared secret
load_dotenv()
#SECRET = os.getenv("SHARED_SECRET", "changeme").encode()
SECRET = "SUPERSECRET"
# === BUILD THE PROCESS OBJECT ===
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
column.length = 0.14
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
process.add_event("grad_start", "flow_sheet.inlet.c", c_gradient_poly, time=t_gradient_start)

cadet = Cadet()
results = cadet.simulate(process)

def save_dict(d, file_name="dict2json.json"):
    with open(file_name, "w") as fp:
        json.dump(d , fp) 
        
# SERIALIZE, ENCODE, SIGN
proc_bytes = dill.dumps(process)
proc_b64 = base64.b64encode(proc_bytes).decode("utf-8")
sig = hmac.new(SECRET, proc_b64.encode("utf-8"), hashlib.sha256).hexdigest()

# SEND REQUEST
url = "http://localhost:8001/simulate"  # Change to Docker host if needed

response = requests.post(url, json={
    "process": proc_b64,
    "signature": sig
})

if response.ok:
    result = response.json()
    result_bytes = base64.b64decode(result["result"])
    simulation_result = dill.loads(result_bytes)

    print("Simulation success")
    print("Time:", simulation_result.solution.column.outlet.time)
    print("Concentration:", simulation_result.solution.column.outlet.solution)
else:
    print("Error:", response.status_code, response.text)
