## README.md

# Cadet API 🍃 — Chromatography simulations as a service

Cadet API wraps the [CADET](https://cadeploy.readthedocs.io/) process‑model
tool-chain behind a HTTPS + JWT‑signed REST interface.
It lets you submit a *dill‑serialised* `CADETProcess.Process`, runs the
simulation in an isolated worker, and streams the results back—digitally
signed so the client can verify integrity.

The clients public key must be registered in the app. Refer to the [Instruction](INSTRUCTIONS.md) for more details.
Pickling and unpicling is secured via private/public key pairs on the server and client side.


| Endpoint      | Method | Purpose                                                          |
| ------------- | ------ | ---------------------------------------------------------------- |
| `/public_key` | GET    | Fetch the server’s signing public key                            |
| `/simulate`   | POST   | Submit a base64‑encoded `process_serialized` payload + signature |

---

## Quick‑start (Docker)

```bash
git clone https://github.com/<you>/cadet_docker.git
cd cadet_docker

# one command does *everything*
./dev_setup.sh          # generates keys, builds the image, runs docker‑compose
```

Open **[https://localhost:8001/docs](https://localhost:8001/docs)** for the interactive Swagger UI.

> *First run note:* the Conda layer with CADET is large—expect a few minutes.

### Requirements

* Docker 20.10+ & Docker Compose v2 (Docker Desktop macOS/Windows or native packages Linux)
* GNU make — optional, but handy.

---

## Manual (Python‑only) development

```bash
conda env create -f environment.yml
conda activate cadet
pytest              # run the unit tests
```

The tests spin up Uvicorn on random localhost ports and exercise the full
signature + simulation pipeline. No Docker needed.

---

## Directory layout

```
app/                FastAPI package  ← imported as `app.*`
  ├─ main.py        – HTTP endpoints
  ├─ utils.py       – crypto & (de)serialisation helpers
  └─ …              – extras
scripts/
  └─ generate_server_keys.py
dev_setup.py        – guarantees ~/.cadet_api/ keystore + self‑signed TLS
dev_setup.sh        – runs ↑ then `docker compose up`
docker-compose_ubuntu.yml
Dockerfile_ubuntu
tests/
```

---

## Key & certificate model

```
~/.cadet_api/
  private_key.pem             (server signing key)
  public_key.pem              (matching public key, exposed at /public_key)
  tls/
      server.key              (TLS private key, self‑signed for dev)
      server.crt
  client_keys/
      <client_id>.pem         (public key per authorised client)
```

`dev_setup.py` builds that tree automatically; override with
`export CADET_KEY_HOME=/path/to/keys` if you prefer another location.

---

## Contributing

1. Fork → feature branch → PR.
2. Run `black`, `ruff`, and `pytest`.
3. Explain **why** the change matters (performance, new model, …).

We follow semantic‑commit prefixes (`feat:`, `fix:`, `docs:` …).

---

## License

GPL3

