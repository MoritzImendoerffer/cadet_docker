import unittest

from app.builder import build_process
from CADETProcess.simulator import Cadet


def example_payload():
    """Return a minimal but complete JSON dictionary for smoke‑testing."""
    return {
        "ComponentSystemParams": {"components": ["A", "B", "C", "D"]},
        "BindingParams": {
            "type": "SMA",
            "name": "SMA",
            "is_kinetic": True,
            "adsorption_rate": [0.0, 35.5, 1.59, 7.7],
            "desorption_rate": [0.0, 1000, 1000, 1000],
            "characteristic_charge": [0.0, 4.7, 5.29, 3.7],
            "steric_factor": [0.0, 11.83, 10.6, 10.0],
            "capacity": 1200,
        },
        "RateModelParams": {
            "name": "column",
            "length": 0.014,
            "diameter": 0.02,
            "bed_porosity": 0.37,
            "particle_radius": 4.5e-5,
            "particle_porosity": 0.75,
            "axial_dispersion": 5.75e-8,
            "film_diffusion": [6.9e-6, 6.9e-6, 6.9e-6, 6.9e-6],
            "pore_diffusion": [7e-10, 6.07e-11, 6.07e-11, 6.07e-11],
            "surface_diffusion": [0.0, 0.0, 0.0, 0.0],
            "cv_load": 2,
            "cv_gradient_start": 6,
            "cv_gradient_dur": 3,
        },
        "InletParams": {"name": "inlet", "flow_rate": 15e-6},
        "OutletParams": {"name": "outlet"},
        "FlowSheetParams": {
            "units": [
                {"name": "inlet"},
                {"name": "column"},
                {"name": "outlet"},
            ],
            "connections": [
                {"from_unit": "inlet", "to_unit": "column"},
                {"from_unit": "column", "to_unit": "outlet"},
            ],
            "product_outlet": "outlet",
        },
        "ProcessParams": {
            "name": "lwe_1",
            "cycle_time_cv": 20,
            "load_volume_mL": 200,
            "flow_rate_ml_min": 15,
            "wash_duration_cv": 4,
            "gradient_duration_cv": 3,
            "c_load": [50.0, 1.0, 1.0, 1.0],
            "c_wash": [50.0, 0.0, 0.0, 0.0],
            "c_elute": [500.0, 0.0, 0.0, 0.0],
        },
    }


class TestSimulation(unittest.TestCase):

    def test_simulate_example_payload(self):
        payload = example_payload()
        process = build_process(payload)
        cadet = Cadet()
        results = cadet.simulate(process)

        self.assertIsNotNone(results, "Simulation returned no result")



if __name__ == "__main__":
    unittest.main()
