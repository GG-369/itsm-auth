# Contrato API itsm-auth

Todas las rutas salvo `POST /auth/login` requieren `Authorization: Bearer <JWT>`.

| Método | Ruta | Roles |
|---|---|---|
| POST | `/auth/login` | Público |
| GET | `/auth/me` | Todos |
| GET | `/usuarios?limite=20&rol=AGENTE&siguiente=...` | ADMIN, AGENTE |
| POST | `/usuarios` | ADMIN |
| GET | `/usuarios/{id}` | ADMIN, AGENTE |
| PUT | `/usuarios/{id}` | ADMIN |
| DELETE | `/usuarios/{id}` | ADMIN |
| GET | `/tenants/actual` | Todos |
| POST | `/archivos/presign-subida` | Todos |
| GET | `/archivos/presign-descarga?key=...` | Todos |

Login JSON: `{"tenant_id":"acme","email":"usuario00001@acme.test","password":"Demo2026!"}`.

Alta de usuario JSON: `{"email":"nuevo@acme.test","nombre":"Nuevo","rol":"SOLICITANTE","password":"ClaveSegura2026"}`. El tenant siempre sale del JWT; nunca del body.

Subida S3 JSON: `{"entidad":"incidentes","id":"inc-acme-000001","archivo":"evidencia.pdf","content_type":"application/pdf"}`. El cliente realiza PUT directo a la URL prefirmada usando el mismo Content-Type.

Authorizer context compartido: `tenant_id`, `usuario_id`, `rol`. El resto de microservicios deben leerlo desde `requestContext.authorizer`.

Éxito: `{"data": ...}`. Listas: `{"data":[],"paginacion":{"limite":20,"siguiente":null}}`. Error: `{"error":{"codigo":"...","mensaje":"..."}}`.
