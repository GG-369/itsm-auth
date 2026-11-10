import json
from decimal import Decimal

def _default(v):
    if isinstance(v, Decimal):
        return int(v) if v % 1 == 0 else float(v)
    raise TypeError()

def response(status, payload):
    return {"statusCode": status, "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Authorization,Content-Type", "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"}, "body": json.dumps(payload, ensure_ascii=False, default=_default)}

def ok(data, status=200, pagination=None):
    body = {"data": data}
    if pagination is not None: body["paginacion"] = pagination
    return response(status, body)

def fail(status, code, message):
    return response(status, {"error": {"codigo": code, "mensaje": message}})

def body(event):
    value = json.loads(event.get("body") or "{}")
    if not isinstance(value, dict): raise ValueError("El body debe ser un objeto JSON.")
    return value
