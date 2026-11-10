import os, boto3
from src.common.http import ok, fail
from src.common.context import auth_context
db=boto3.resource("dynamodb")
def current_tenant(event,context):
    try:
        a=auth_context(event); item=db.Table(os.environ["TENANTS_TABLE"]).get_item(Key={"tenant_id":a["tenant_id"]}).get("Item")
        return ok(item) if item and item.get("activo") else fail(404,"TENANT_NO_ENCONTRADO","Tenant no encontrado o inactivo.")
    except PermissionError as e: return fail(401,"NO_AUTENTICADO",str(e))
    except Exception: return fail(500,"DB_ERROR","No se pudo consultar el tenant.")
