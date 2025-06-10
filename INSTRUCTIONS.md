## INSTRUCTIONS.md


> **Note:** This is an early development version, developed by a scientist not a software engineer. If you find critical bugs. Please write me via GitHub

---

### 1 — Local dev loop

```bash
./dev_setup.sh            # (re)build image, ensure ~/.cadet_api exists
docker compose logs -f    # tail the API
pytest -q                 # run tests in another shell
```

`dev_setup.sh` performs two steps:

| Step | Script         | Details                                         |
| ---- | -------------- | ----------------------------------------------- |
| ①    | `dev_setup.py` | • creates `~/.cadet_api` (or `$CADET_KEY_HOME`) |

```
                    • generates RSA‑4096 signing key‑pair (once)  
                    • issues a self‑signed TLS cert in `tls/` |
```

\| ②    | `docker compose`  | builds the **api** image and launches the stack |

---

### 2 — Package & import strategy

* Source keeps `app/`, imported as a real package (`app.main`, `app.utils`, …).
* Use **relative** or **fully‑qualified** imports:

```python
from .utils import sign_bytes        # ✅ relative
# or
from app.utils import sign_bytes     # ✅ absolute
```

Never `from utils import …` — that only works when CWD == repo root.

* In the image code lives at `/code/app`, `WORKDIR /code`, and Compose runs:

```yaml
command: >
  gunicorn app.main:app --workers 2
         --worker-class uvicorn.workers.UvicornWorker
         --bind 0.0.0.0:8001
         --timeout 0
         --keyfile  /certs/server.key
         --certfile /certs/server.crt
```

---

### 3 — Tests

* Tests live in `tests/` and use **pytest**.
* Each test grabs a free port, writes keys to a temp-dir, and starts Uvicorn.
* Helpers: `load_private_pem`, `sign_bytes` in `app.utils`.

Speed tip: wrap server start‑up in a `@pytest.fixture(scope="module")` when adding many tests.

---

### 4 — Key hygiene

* **Never** commit secrets. Generate locally via `scripts/generate_server_keys.py` or `openssl genrsa`.
* Client public keys → `client_keys/<client_id>.pem`; `client_id` must match `^[A-Za-z0-9_-]+$`.


---

Happy hacking — and thanks for contributing! 🚀
