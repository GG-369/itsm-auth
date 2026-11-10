import os, re, boto3
from src.common.http import ok, fail, body
from src.common.context import auth_context
s3=boto3.client("s3")
BUCKET=os.getenv("ATTACHMENTS_BUCKET","")
SAFE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
TYPES={"application/pdf","image/jpeg","image/png","text/plain","application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
def segment(v):
    if not isinstance(v,str) or not SAFE.fullmatch(v) or v in {".",".."}: raise ValueError("Segmento de ruta inválido.")
    return v
def presign_upload(event,context):
    try:
        a=auth_context(event); d=body(event); entity=segment(d.get("entidad")); ident=segment(d.get("id")); name=segment(d.get("archivo")); typ=d.get("content_type","application/octet-stream")
        if typ not in TYPES: return fail(400,"TIPO_NO_PERMITIDO","Tipo de archivo no permitido.")
        key=f"{a['tenant_id']}/{entity}/{ident}/{name}"
        url=s3.generate_presigned_url("put_object",Params={"Bucket":BUCKET,"Key":key,"ContentType":typ},ExpiresIn=300)
        return ok({"url":url,"key":key,"metodo":"PUT","expira_en_segundos":300})
    except PermissionError as e: return fail(401,"NO_AUTENTICADO",str(e))
    except ValueError as e: return fail(400,"VALIDACION",str(e))
    except Exception: return fail(500,"S3_ERROR","No se pudo generar URL de subida.")
def presign_download(event,context):
    try:
        a=auth_context(event); key=(event.get("queryStringParameters") or {}).get("key","")
        if not key.startswith(a["tenant_id"]+"/") or ".." in key.split("/"): return fail(403,"TENANT_INVALIDO","No puedes acceder a archivos de otro tenant.")
        url=s3.generate_presigned_url("get_object",Params={"Bucket":BUCKET,"Key":key},ExpiresIn=300)
        return ok({"url":url,"key":key,"expira_en_segundos":300})
    except PermissionError as e: return fail(401,"NO_AUTENTICADO",str(e))
    except Exception: return fail(500,"S3_ERROR","No se pudo generar URL de descarga.")
