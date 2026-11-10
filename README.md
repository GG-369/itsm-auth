# itsm-auth

Microservicio de autenticación, usuarios y tenants del SaaS ITSM (CS2032 Cloud Computing).

## Stack
Python 3.12 · AWS Lambda · API Gateway REST · DynamoDB on-demand · S3 privado · SSM Parameter Store · JWT HS256 · Serverless Framework 3.

SNS/SQS/DLQ quedan fuera de este incremento, pendientes de revisión del profesor y del stack de infraestructura del Integrante 1.

## Preparación (Windows PowerShell)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-seed.txt
npm install
npm install -g serverless@3
```

Configura credenciales AWS Academy/Learner Lab con el método indicado en clase y renuévalas antes de desplegar. El stack declara permisos mínimos para DynamoDB y S3. Si AWS Academy bloquea la creación del rol IAM, configura el rol `LabRole` existente en `provider.iam.role` de `serverless.yml` (consulta su ARN real en Learner Lab y no lo inventes); al usar un rol existente, asegúrate de que tenga permisos para DynamoDB, S3 y CloudWatch Logs.

## Secreto y despliegue
```powershell
python scripts/bootstrap_ssm.py --stage dev --region us-east-1
serverless deploy --stage dev --region us-east-1
```
El secreto se crea en `/itsm-auth/dev/jwt-secret` como SSM SecureString. El despliegue publica el ARN del Authorizer en `/itsm-auth/dev/authorizer-arn`.

## Seed demo
```powershell
python seed/seed_users.py --stage dev --per-tenant 10000
```
Tenants: `acme`, `globex`, `initech`. Admin de cada tenant: `usuario00001@{tenant}.test`. Contraseña demo: `Demo2026!`. IDs: `usr-{tenant}-{n:05d}`. Para cambiar la clave, define `$env:DEMO_PASSWORD` antes de ejecutar el seed.

## Decisiones de seguridad
- El tenant se toma siempre del JWT validado, nunca del body/query.
- La tabla usuarios usa PK `tenant_id`, SK `usuario_id`, GSI `GSI-email` (PK tenant_id, SK email).
- No se devuelven hashes de contraseña; se usa PBKDF2-HMAC-SHA256.
- DELETE desactiva lógicamente al usuario.
- Bucket privado, bloqueo de acceso público, cifrado AES256 y URLs prefirmadas de 5 minutos.
- El GSI no garantiza unicidad transaccional de email ante escrituras concurrentes; para la demo se valida previamente.
- Ajustar CORS a los dominios reales antes de producción.

## Importante
Primero validar el contrato T01 del equipo (región, runtime, nombres y rol IAM). El plan de trabajo advierte que AWS Academy puede restringir la creación de roles IAM.
