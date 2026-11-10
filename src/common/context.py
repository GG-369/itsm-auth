def auth_context(event):
    auth = event.get("requestContext", {}).get("authorizer") or {}
    if not all(auth.get(k) for k in ("tenant_id", "usuario_id", "rol")): raise PermissionError("Contexto de autenticación ausente.")
    return auth
