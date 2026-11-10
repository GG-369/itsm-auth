import os
import base64
import hashlib
import hmac
import secrets

from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt


def hash_password(password):
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")

    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        310000
    )

    return "pbkdf2_sha256$310000$%s$%s" % (
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode()
    )


def verify_password(password, encoded):
    try:
        alg, rounds, salt, expected = encoded.split("$")

        if alg != "pbkdf2_sha256":
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            base64.urlsafe_b64decode(salt),
            int(rounds)
        )

        return hmac.compare_digest(
            actual,
            base64.urlsafe_b64decode(expected)
        )

    except Exception:
        return False


@lru_cache(maxsize=1)
def secret():
    # 1. Permitir un secreto local durante pruebas.
    local_secret = os.getenv("JWT_SECRET")

    if local_secret:
        return local_secret

    # 2. Obtener la ruta del secreto en AWS Parameter Store.
    parameter_name = os.getenv("JWT_SECRET_PARAMETER")

    if not parameter_name:
        raise RuntimeError("JWT_SECRET_PARAMETER no configurado")

    # 3. Recuperar el secreto desde AWS Systems Manager.
    import boto3

    ssm = boto3.client("ssm")

    response = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )

    value = response["Parameter"]["Value"]

    if not value:
        raise RuntimeError("JWT secret vacío en Parameter Store")

    return value


def issue_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "iss": os.getenv("JWT_ISSUER", "itsm-auth"),
        "sub": user["usuario_id"],
        "tenant_id": user["tenant_id"],
        "rol": user["rol"],
        "iat": now,
        "exp": now + timedelta(
            hours=int(os.getenv("JWT_EXP_HOURS", "8"))
        )
    }

    return jwt.encode(
        payload,
        secret(),
        algorithm="HS256"
    )


def decode_token(token):
    return jwt.decode(
        token,
        secret(),
        algorithms=["HS256"],
        issuer=os.getenv("JWT_ISSUER", "itsm-auth"),
        options={
            "require": [
                "iss",
                "sub",
                "iat",
                "exp",
                "tenant_id",
                "rol"
            ]
        }
    )


def cursor_encode(key):
    if not key:
        return None

    import json

    return base64.urlsafe_b64encode(
        json.dumps(key).encode()
    ).decode()


def cursor_decode(value):
    if not value:
        return None

    import json

    try:
        return json.loads(
            base64.urlsafe_b64decode(value).decode()
        )

    except Exception:
        raise ValueError("Cursor de paginación inválido.")