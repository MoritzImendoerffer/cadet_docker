# CADET Simulation Microservice

This project provides a FastAPI-based microservice that runs simulations using [CADETProcess](https://github.com/modsim/CADET) based on RSA-signed payloads. Clients submit dill-pickled `Process` objects signed with their private keys. The server verifies signatures, runs the simulation, and returns signed results.

The clients public key should either reside in <root>/client_keys or in a folder defined by CLIENT_KEYS_DIR

---

## 📦 Features

- POST `/simulate`: Simulate a CADET `Process` instance
- GET `/public_key`: Get the server’s public key
- RSA-based signature verification
- Supports end-to-end test suite with isolated keypairs

---

## 🛠 Requirements

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Server

By default, the server uses environment variables to configure keys:

```bash
export PRIVATE_KEY_PATH=private_key.pem
export PUBLIC_KEY_PATH=public_key.pem
export CLIENT_KEYS_DIR=client_keys
```

Start the server:

```bash
uvicorn app.main:app --reload
```

---

## 🧪 Running Tests

Tests are located in the `tests/` folder and use `pytest`.

```bash
# Run all tests
pytest tests/
```

To enable test discovery in **VS Code**:
- Press `Ctrl+Shift+P` → "Python: Configure Tests"
- Choose `pytest`, then `tests` as the folder

Ensure `.vscode/settings.json` contains:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

---

## 🗝️ Client Integration

Clients must:

1. Serialize a `CADETProcess.Process` instance with `dill`
2. Sign the serialized bytes using their private RSA key
3. Send a POST to `/simulate` with:
   - `client_id`: Matches a public key file in `client_keys/<client_id>.pem`
   - `process_serialized`: Base64-encoded dill blob
   - `signature`: Base64-encoded RSA signature

Example payload:

```json
{
  "client_id": "acme",
  "process_serialized": "<base64-dill>",
  "signature": "<base64-signature>"
}
```

---

## 📁 Project Structure

```
app/
 ├── main.py          # FastAPI app
 ├── utils.py         # Key handling and serialization
client_keys/          # Public keys per client
tests/
 └── test_simulate.py # Tests for the /simulate endpoint
```

---

## 📝 License

GPL3
