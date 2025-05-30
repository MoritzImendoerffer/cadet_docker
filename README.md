# 🧪 CADET Simulation API – Modular FastAPI for Chromatography Modeling

This project provides a modular, JSON-driven API for setting up and simulating chromatography processes using the [CADET Process](https://cadet-process.readthedocs.io/en/latest/) Python library.

The API is implemented in **FastAPI**, and all simulation configurations are expressed using structured **Pydantic models** — enabling clean validation, OpenAPI docs, and future GUI or CLI integrations.

---

## 🚀 Features

- ✅ RESTful API to simulate chromatography processes
- ✅ Fully parameterized load-wash-elute (LWE) configuration
- ✅ Clean Pydantic models with OpenAPI generation
- ✅ Structured support for:
  - `ComponentSystem`
  - `StericMassAction` binding
  - `GeneralRateModel` columns
  - `Inlet`, `Outlet`, and `FlowSheet`
- 🧱 Easily extendable to other CADET models

---

## ⚙️ Requirements

- Python 3.10+
- `cadet-process`
- `fastapi`, `uvicorn`
- `pydantic`, `numpy`

Install:

```bash
pip install -r requirements.txt
# or use conda and install cadet-process from source
