# 🧪 Simulation API

This FastAPI application allows you to send serialized Python `Process` objects to a server for simulation and receive results in a secure and efficient manner. It is designed to be used with Docker and supports HMAC-based authentication to verify the integrity and authenticity of the requests.

---

## 🚀 Features

- Accepts serialized and signed `Process` objects.
- Secure communication using HMAC-SHA256.
- Supports custom simulation workflows via class-based architecture.
- Lightweight test endpoint for health checks or dev integration.

---

## 📦 API Endpoints

### `POST /simulate`

**Description:** Accepts a base64-encoded and signed `Process` object, executes its `simulate()` method, and returns the results.

#### Request Body

```json
{
  "process": "<base64-encoded dill-serialized Process object>",
  "signature": "<HMAC SHA256 signature>"
}
```

#### Response

```json
{
  "result": "<base64-encoded dill-serialized simulation result>"
}
```

---

### `POST /test`

**Description:** Simple test endpoint to verify server availability.

#### Response

```json
{
  "result": "Hurra"
}
```

---

## 🔐 Security

The request is validated using an HMAC-SHA256 signature. The server calculates a hash from the payload using a shared secret and compares it to the provided signature to verify authenticity.

```python
expected = hmac.new(SECRET, proc_b64.encode(), hashlib.sha256).hexdigest()
```

---

## 🛠️ Setup

### Requirements

Requirements are defined in environment.yml

### Install dependencies

docker buildx build -t cadet-api-ubuntu --file Dockerfile_ubuntu .

### Run the server


docker run -d -p 8000:8000 cadet-api-ubuntu

Check: 0.0.0.0:8000/docs
---

## 📤 Sending a Process

You must create a `Process` class on the client side with a `simulate()` method, serialize it with `dill`, encode it with base64, and sign the payload with the shared secret.

See [cadet-process LWE example](https://cadet-process.readthedocs.io/en/latest/examples/load_wash_elute/lwe_concentration.html) for best practices.

---

## 📌 TODO

- [ ] Replace the hardcoded secret:

    ```python
    # Replace:
    SECRET = "SUPERSECRET"

    # With:
    import os
    SECRET = os.getenv("SHARED_SECRET", "changeme").encode()
    ```

- [ ] Use `.env` for configuration and secrets. 

- [ ] Implement logging for better observability.

- [ ] Add unit and integration tests.

- [ ] Add client SDK or usage examples.

---

## 📄 License

GPL3
