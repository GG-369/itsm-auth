import argparse
import os
import boto3

from datetime import datetime, timezone
from faker import Faker
from src.common.security import hash_password

TENANTS = {
    "acme": "Acme Corp",
    "globex": "Globex Corporation",
    "initech": "Initech"
}

fake = Faker("es_MX")


def run(stage="dev", per_tenant=10000, password="Demo2026!"):
    db = boto3.resource("dynamodb", region_name="us-east-1")

    users = db.Table(f"itsm-auth-{stage}-usuarios")
    tenants = db.Table(f"itsm-auth-{stage}-tenants")

    pwd = hash_password(password)
    now = datetime.now(timezone.utc).isoformat()

    for tid, name in TENANTS.items():

        tenants.put_item(
            Item={
                "tenant_id": tid,
                "nombre": name,
                "plan": "PRO",
                "activo": True,
                "creado_en": now
            }
        )

        with users.batch_writer(
            overwrite_by_pkeys=["tenant_id", "usuario_id"]
        ) as batch:

            for n in range(1, per_tenant + 1):

                batch.put_item(
                    Item={
                        "tenant_id": tid,
                        "usuario_id": f"usr-{tid}-{n:05d}",
                        "email": f"usuario{n:05d}@{tid}.test",
                        "nombre": fake.name(),
                        "rol": (
                            "ADMIN" if n == 1
                            else "AGENTE" if n <= 101
                            else "SOLICITANTE"
                        ),
                        "departamento": fake.job(),
                        "password_hash": pwd,
                        "activo": True,
                        "creado_en": now
                    }
                )

        print(f"{tid}: {per_tenant} usuarios cargados")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--stage", default="dev")
    parser.add_argument("--per-tenant", type=int, default=10000)
    parser.add_argument(
        "--password",
        default=os.getenv("DEMO_PASSWORD", "Demo2026!")
    )

    args = parser.parse_args()

    run(args.stage, args.per_tenant, args.password)
