from base64 import b64encode, b64decode
import dill


def dumps(obj) -> bytes:
    return dill.dumps(obj)


def loads(blob: bytes):
    return dill.loads(blob)


def dumps_b64(obj) -> str:
    return b64encode(dill.dumps(obj)).decode()


def loads_b64(txt: str):
    return dill.loads(b64decode(txt))
