from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import base64
import dill
import hmac
import hashlib
from .builder import build_process_from_params
from .models.process import ProcessParams

load_dotenv()
#SECRET = os.getenv("SHARED_SECRET", "changeme").encode()
SECRET = "SUPERSECRET"
app = FastAPI()

# @app.post("/simulate")
# async def simulate(request: Request):
#     data = await request.json()
#     proc_b64 = data.get("process")
#     signature = data.get("signature")

#     if not proc_b64 or not signature:
#         raise HTTPException(status_code=400, detail="Missing process or signature")

#     expected = hmac.new(SECRET, proc_b64.encode(), hashlib.sha256).hexdigest()
#     if not hmac.compare_digest(expected, signature):
#         raise HTTPException(status_code=403, detail="Invalid signature")

#     process_bytes = base64.b64decode(proc_b64.encode())
#     process = dill.loads(process_bytes)

#     results = process.simulate()
#     result_bytes = dill.dumps(results)
#     result_b64 = base64.b64encode(result_bytes).decode()

#     return {"result": result_b64}

@app.post("/test")
async def test(request: Request):
    return {"result": "Hurra"}

@app.post("/simulate")
def simulate(params: ProcessParams):
    process = build_process_from_params(params)
    result = process.simulate()

    return {
        "time": result.solution.column.outlet.time.tolist(),
        "outlet_concentration": result.solution.column.outlet.solution.tolist()
    }