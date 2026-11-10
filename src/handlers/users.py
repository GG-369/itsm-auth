import os, boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from src.common.http import ok, fail, body
from src.common.context import auth_context
from src.common.security import hash_password, cursor_encode, cursor_decode

db = boto3.resource("dynamodb")
def table(): return db.Table(os.environ["USERS_TABLE"])
ROLES = {"ADMIN","AGENTE","SOLICITANTE"}
def require(event, roles):
    a = auth_context(event)
    if a["rol"] not in roles: raise PermissionError("No tienes permisos para esta operación.")
    return a
def safe(x):
    x = dict(x); x.pop("password_hash",None); return x

def list_users(event, context):
    try:
        a=require(event,{"ADMIN","AGENTE"}); q=event.get("queryStringParameters") or {}; limit=min(max(int(q.get("limite",20)),1),100)
        args={"KeyConditionExpression":Key("tenant_id").eq(a["tenant_id"]),"Limit":limit}
        cursor=cursor_decode(q.get("siguiente"))
        if cursor: args["ExclusiveStartKey"]=cursor
        if q.get("rol"):
            if q["rol"] not in ROLES: return fail(400,"VALIDACION","Rol inválido.")
            args["FilterExpression"]="#r = :r"; args["ExpressionAttributeNames"]={"#r":"rol"}; args["ExpressionAttributeValues"]={":r":q["rol"]}
        result=table().query(**args)
        return ok([safe(x) for x in result.get("Items",[])],pagination={"limite":limit,"siguiente":cursor_encode(result.get("LastEvaluatedKey"))})
    except PermissionError as e: return fail(403,"PROHIBIDO",str(e))
    except Exception: return fail(400,"VALIDACION","Parámetros de consulta inválidos.")

def create_user(event, context):
    try:
        a=require(event,{"ADMIN"}); d=body(event); email=str(d.get("email","")).strip().lower(); name=d.get("nombre"); role=d.get("rol","SOLICITANTE"); password=d.get("password")
        if "@" not in email or not isinstance(name,str) or not name.strip() or role not in ROLES or not isinstance(password,str): return fail(400,"VALIDACION","Datos de usuario inválidos.")
        existing=table().query(IndexName="GSI-email",KeyConditionExpression=Key("tenant_id").eq(a["tenant_id"]) & Key("email").eq(email),Limit=1).get("Items",[])
        if existing: return fail(409,"EMAIL_DUPLICADO","El email ya existe en este tenant.")
        uid=d.get("usuario_id") or "usr-"+a["tenant_id"]+"-"+datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        item={"tenant_id":a["tenant_id"],"usuario_id":uid,"email":email,"nombre":name.strip(),"rol":role,"departamento":d.get("departamento",""),"password_hash":hash_password(password),"activo":True,"creado_en":datetime.now(timezone.utc).isoformat()}
        table().put_item(Item=item,ConditionExpression="attribute_not_exists(tenant_id) AND attribute_not_exists(usuario_id)")
        return ok(safe(item),201)
    except PermissionError as e: return fail(403,"PROHIBIDO",str(e))
    except ValueError as e: return fail(400,"VALIDACION",str(e))
    except Exception: return fail(500,"DB_ERROR","No se pudo crear el usuario.")

def get_user(event, context):
    try:
        a=require(event,{"ADMIN","AGENTE"}); uid=event["pathParameters"]["id"]; item=table().get_item(Key={"tenant_id":a["tenant_id"],"usuario_id":uid}).get("Item")
        return ok(safe(item)) if item else fail(404,"NO_ENCONTRADO","Usuario no encontrado.")
    except PermissionError as e: return fail(403,"PROHIBIDO",str(e))
    except Exception: return fail(500,"DB_ERROR","No se pudo consultar el usuario.")

def update_user(event, context):
    try:
        a=require(event,{"ADMIN"}); uid=event["pathParameters"]["id"]; d=body(event); allowed={k:v for k,v in d.items() if k in {"nombre","rol","activo","departamento"}}
        if not allowed or ("rol" in allowed and allowed["rol"] not in ROLES): return fail(400,"VALIDACION","Campos editables o rol inválidos.")
        if "activo" in allowed and not isinstance(allowed["activo"], bool): return fail(400,"VALIDACION","activo debe ser booleano.")
        if "nombre" in allowed and (not isinstance(allowed["nombre"], str) or not allowed["nombre"].strip()): return fail(400,"VALIDACION","nombre no puede estar vacío.")
        names={f"#k{i}":k for i,k in enumerate(allowed)}; vals={f":v{i}":v for i,v in enumerate(allowed.values())}; expr="SET "+", ".join(f"#k{i} = :v{i}" for i in range(len(allowed)))
        out=table().update_item(Key={"tenant_id":a["tenant_id"],"usuario_id":uid},UpdateExpression=expr,ExpressionAttributeNames=names,ExpressionAttributeValues=vals,ConditionExpression="attribute_exists(tenant_id)",ReturnValues="ALL_NEW")
        return ok(safe(out["Attributes"]))
    except PermissionError as e: return fail(403,"PROHIBIDO",str(e))
    except Exception: return fail(404,"NO_ENCONTRADO","No se pudo actualizar el usuario.")

def deactivate_user(event, context):
    try:
        a=require(event,{"ADMIN"}); uid=event["pathParameters"]["id"]
        out=table().update_item(Key={"tenant_id":a["tenant_id"],"usuario_id":uid},UpdateExpression="SET activo = :v",ExpressionAttributeValues={":v":False},ConditionExpression="attribute_exists(tenant_id)",ReturnValues="ALL_NEW")
        return ok(safe(out["Attributes"]))
    except PermissionError as e: return fail(403,"PROHIBIDO",str(e))
    except Exception: return fail(404,"NO_ENCONTRADO","No se pudo desactivar el usuario.")
