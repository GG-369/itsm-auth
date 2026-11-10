from src.common.security import decode_token

def authorize(event, context):
    token = (event.get("authorizationToken") or "").strip()
    if token.lower().startswith("bearer "): token = token[7:].strip()
    try:
        claims = decode_token(token)
        if claims["rol"] not in {"ADMIN", "AGENTE", "SOLICITANTE"}: raise ValueError()
        arn = event["methodArn"].split(":")
        api = arn[5].split("/")[0]
        resource = f"arn:aws:execute-api:{arn[3]}:{arn[4]}:{api}/*/*"
        return {"principalId": claims["sub"], "policyDocument": {"Version":"2012-10-17","Statement":[{"Action":"execute-api:Invoke","Effect":"Allow","Resource":resource}]}, "context":{"tenant_id":claims["tenant_id"],"usuario_id":claims["sub"],"rol":claims["rol"]}}
    except Exception:
        raise Exception("Unauthorized")
