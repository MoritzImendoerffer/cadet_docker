import requests
import base64
import dill
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

API_BASE = "http://localhost:8001"

def get_public_key():
    response = requests.get(f"{API_BASE}/public_key")
    response.raise_for_status()
    public_key_pem = response.json()["public_key_pem"]
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode(), backend=default_backend()
    )
    return public_key


def call_simulate():
    dummy_payload = {
        "ComponentSystemParams": {...},  # Fill in with actual test data
        "BindingParams": {...},
        "RateModelParams": {...},
        "InletParams": {...},
        "OutletParams": {...},
        "FlowSheetParams": {...},
        "ProcessParams": {...},
    }

    response = requests.post(f"{API_BASE}/simulate", json=dummy_payload)
    response.raise_for_status()
    return response.json()


def verify_signature(public_key, serialized_data_b64, signature_b64):
    serialized_data = base64.b64decode(serialized_data_b64)
    signature = base64.b64decode(signature_b64)

    try:
        public_key.verify(
            signature,
            serialized_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        print("Signature is valid.")
        return dill.loads(serialized_data)
    except Exception as e:
        print("Signature verification failed:", e)
        return None

if __name__ == "__main__":
    public_key = get_public_key()
    sim_response = call_simulate()

    verified_data = verify_signature(
        public_key,
        sim_response["results_serialized"],
        sim_response["signature"]
    )

    if verified_data is not None:
        print("Verified simulation result:", verified_data)
