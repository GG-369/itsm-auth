import os, boto3
from boto3.dynamodb.conditions import Key
from src.common.http import ok, fail, body
from src.common.context import auth_context
from src.common.security import verify_password, issue_token

db = boto3.resource("dynamodb")
def users(): return db.Table(os.environ["USERS_TABLE"])

def login(event, context):
    try:
        data = body(event); tenant = data.get("tenant_id"); email = str(data.get("email","")).strip().lower(); password = data.get("password")
        if not tenant or not email or not isinstance(password,str): return fail(400,"VALIDACION","tenant_id, email y password son obligatorios.")
        tenant_item = db.Table(os.environ["TENANTS_TABLE"]).get_item(Key={"tenant_id":tenant}).get("Item")
        if not tenant_item or not tenant_item.get("activo"):
            return fail(401,"CREDENCIALES_INVALIDAS","Credenciales incorrectas.")
        result = users().query(IndexName="GSI-email",KeyConditionExpression=Key("tenant_id").eq(tenant) & Key("email").eq(email),Limit=1)
        found = result.get("Items",[])
        if not found or not found[0].get("activo") or not verify_password(password,found[0].get("password_hash","")): return fail(401,"CREDENCIALES_INVALIDAS","Credenciales incorrectas.")
        user = found[0]; safe = {k:v for k,v in user.items() if k != "password_hash"}
        return ok({"token":issue_token(user),"tipo":"Bearer","usuario":safe})
    except ValueError as e: return fail(400,"VALIDACION",str(e))
    except Exception: return fail(500,"AUTH_ERROR","No se pudo completar el inicio de sesión.")

def me(event, context):
    try:
        a = auth_context(event); item = users().get_item(Key={"tenant_id":a["tenant_id"],"usuario_id":a["usuario_id"]}).get("Item")
        if not item or not item.get("activo"): return fail(401,"USUARIO_INACTIVO","Usuario inactivo.")
        item.pop("password_hash",None); return ok(item)
    except PermissionError as e: return fail(401,"NO_AUTENTICADO",str(e))
    except Exception: return fail(500,"DB_ERROR","No se pudo consultar el usuario.")
