# E-Starter

E-Starter is a simple and easy-to-use backend framework designed for small to medium-sized projects. It provides a robust starting point for developers looking to jumpstart their application development without dealing with complex configurations.

For AI-assisted development, follow the [project development rules](AGENTS.md).

### Prerequisites

- Python (Python 3.12 recommended)
- Linux (Ubuntu 20.04 recommended)

## Getting Started

Follow these simple steps to get a local copy up and running.

### Clone the Repository

```bash
git clone https://github.com/Accec/E-Start-Backend
```

### Installation

1. Install the dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```
2. Navigate to the config directory:
   ```bash
   cd src/core/config
   ```
3. Copy the example configuration file and rename it:
   ```bash
   cp sample.yaml <CONFIG_NAME>.yaml
   ```
4. Open your configuration file with a text editor (like `vi`) and set the configuration.
   The YAML files now point to [schema.json](src/core/config/schema.json), so IDEs/YAML language servers can provide key completion and validation:
   Configuration is grouped by purpose, for example `jwt.secret_key`, `redis.url`, `mysql.database`, and `server.workers`.
   ```bash
   vi <CONFIG_NAME>.yaml
   ```
5. Navigate back to the project root:
   ```bash
   cd ../../..
   ```
6. Copy the environment template and open the local file with a text editor (like `vi`):
   ```bash
   cp src/.env.example src/.env
   vi src/.env
   ```
7. Set the mode to development by updating the MODE environment variable:
   ```bash
   MODE=<CONFIG_NAME>
   ```
8. Initialize the database and create an admin user:
   ```bash
   python src/main.py init_database
   python src/main.py create_admin --username <USERNAME> --password <PASSWORD>
   ```

### Configuration

`base.yaml`, `sample.yaml`, `schema.json`, and `src/.env.example` are versioned templates.
Local `.env` files and mode-specific YAML files such as `dev.yaml` are ignored;
create your own from the templates and keep credentials out of Git.

The YAML files use seven sections:

| Section | Settings |
| --- | --- |
| `app` | `name`, `debug`, `timezone` |
| `server` | `host`, `port`, `workers`, `forwarded_secret`, `cors_domains` |
| `paths` | `relative`, `uploads`, `logs`, `migrations` |
| `jwt` | `secret_key`, `exp_time` (seconds) |
| `mysql` | `host`, `port`, `username`, `password`, `database` |
| `redis` | `url` |
| `tools` | `pip` |

For example, a partial mode configuration can override only the settings it needs:

```yaml
# yaml-language-server: $schema=./schema.json
app:
  debug: true

server:
  host: localhost
  port: 8000
  workers: 1

mysql:
  host: 127.0.0.1
  database: demo
```

`base.yaml` supplies shared settings, followed by the file selected through `MODE`.
Sections merge field by field; lists such as `server.cors_domains` replace the
base list rather than extending it. Omitted settings use inherited values or
the existing defaults. Explicit `null` section or field values, unknown sections
or keys, and incorrect value types are rejected. If the selected mode file does not exist, loading
falls back to `sample.yaml` as before.

Custom YAML files must migrate to this nested format; legacy flat keys are not
accepted. Python consumers are unchanged: `server.workers` still populates
`config.sanic_workers`, and `mysql.host` still populates `config.mysql_host`.
Existing `Config(...)` constructor arguments remain valid.

### HTTP Workers

Start the HTTP server from the project root:

```bash
python src/main.py server
```

Omitting `server` starts the same HTTP mode.

Set `server.workers` in your YAML config to control the number of HTTP worker processes.

- A value of `1` runs a single HTTP worker.
- A value of `2` or higher enables multi-worker HTTP mode.

The scheduler is always a separate process now. HTTP mode never starts background jobs, regardless of worker count. Run the scheduler separately:

```bash
python src/main.py scheduler
```

Each HTTP worker creates its own application dependencies through `create_http_app`.
The scheduler process creates an application for route discovery without opening an HTTP listener; its entrypoint owns scheduler startup and shutdown.

### Database Migrations

This project now uses Aerich for database migrations.

- Check database reachability and credentials before running Aerich:
  ```bash
  python src/main.py migration_doctor
  ```

- First-time bootstrap on an empty database:
  ```bash
  python src/main.py init_database
  ```
- Initialize migration history for a repository that does not have committed migrations yet:
  ```bash
  python src/main.py migration_init_migrations
  ```
- Create the initial schema directly from the current models only when you are bootstrapping migration history for the first time:
  ```bash
  python src/main.py migration_init_db
  ```
- Create a new migration after changing models:
  ```bash
  python src/main.py migration_migrate --name <MIGRATION_NAME>
  ```
- Apply unapplied migrations:
  ```bash
  python src/main.py migration_upgrade
  ```
- Inspect migration state:
  ```bash
  python src/main.py migration_history
  python src/main.py migration_heads
  ```
- Seed default identity-access data again if needed:
  ```bash
  python src/main.py seed_identity_access
  ```

Migration config lives in `pyproject.toml`, uses `infra.database.TORTOISE_ORM`, and stores generated files under `migrations/demo/`.
Schema history now lives in `migrations/` only. Legacy SQL bootstrap files have been removed.

### Operational Endpoints

- Liveness:
  ```text
  GET /api/v1/system/health
  ```
- Readiness:
  ```text
  GET /api/v1/system/ready
  ```

`/health` only reports that the process is alive.
`/ready` checks the database and Redis dependencies and returns HTTP `503` when one of them is unavailable.

Congratulations! Now, you're all set to start using demo for your project.

### Project Structure

The project groups related business capabilities into domains without requiring
every domain to contain four architectural layers:

```text
src/
  app.py                 # Sanic application factory and explicit route dependencies
  main.py                # command dispatch and HTTP/scheduler process lifecycle
  core/                  # shared conventions, config, constants, HTTP helpers
  infra/                 # database, Redis, scheduler, security, logging and web adapters
  domains/
    identity_access/     # users, roles, permissions, endpoints
      controller/
        router.py        # one explicit route-registration entrypoint
        common.py        # shared nested schemas and field validation
        support.py       # HTTP mapping helpers
        auth/            # api.py + schemas.py
        dashboard/       # api.py + schemas.py
        users/           # api.py + schemas.py
        roles/           # api.py + schemas.py
        permissions/     # api.py + schemas.py
        endpoints/       # api.py + schemas.py
      services/          # business operations; no use_cases subdirectory
      repositories/      # one ORM repository module per resource
      models.py          # ORM models
      ports.py           # dependency protocols
      errors.py
      policies.py
      audit.py           # request metadata and audit recording
      cache.py
      security.py
    audit/               # audit log use cases and persistence
      controller/
        router.py
        logs/            # api.py + schemas.py
      services/
        logs.py
      repositories/
        logs.py
      models.py
      ports.py
      records.py         # audit records and paginated results
    operations/          # operational jobs and scheduler management
      controller/
        router.py
        jobs/            # api.py + schemas.py
      services/
        jobs.py
      ports.py
      jobs.py            # scheduler contracts and validation
      scheduler_gateway.py
  middleware/            # request-scoped cross-cutting behavior
  scripts/ops/           # operator CLI and manual scripts
  tests/                 # structural and regression checks
migrations/              # Aerich migration root
  demo/                  # versioned migration files for the demo app
docs/legacy/             # notes about retired pre-migration artifacts
```

`create_app(config, redis_client, scheduler)` constructs services as local variables,
passes them directly to route registration, and returns only the Sanic application.
There is no Bootstrap container or Runtime wrapper. Database setup belongs to
`infra.database`, logging setup to `infra.logging`, and route wrappers to
`infra.web.routing`.

Domain route registration receives only the services and JWT dependency it uses.
Controllers and services use explicit constructor arguments rather than a global
service registry. Admin and role initialization commands construct their own
business service without building unrelated HTTP, Redis, or scheduler dependencies.
Every resource keeps its HTTP handlers and schemas in adjacent files, including
domains with only one resource. Each domain's `controller.router.register_routes`
receives explicit dependencies and calls its resource registration functions once.
The application imports this entrypoint directly; there are no intermediate
admin/user registration packages. Existing Blueprint prefixes and authorization
rules still distinguish admin and user endpoints.

All domain package directories have an `__init__.py`, omitted from the tree above.
These files are empty or contain a package docstring; they do not re-export
services or routes. Importing a domain does not create runtime resources or start
background work. Services depend on protocols and business contracts, not HTTP
schemas or concrete adapters. Services always use `services/<resource-or-capability>.py`,
and repositories use `repositories/<resource>.py`, even when a domain has only one
implementation. Operations uses a scheduler gateway rather than an ORM repository,
so it does not contain an empty repository package.

ORM model discovery uses `core.persistence.ORM_MODEL_MODULES`, which points to
`domains.identity_access.models` and `domains.audit.models`. Moving these Python
modules does not change database tables, relationships, app labels, or migration
history. Old Python import paths are not retained as compatibility aliases.

### Development Conventions

Use **HTTP method + singular resource + parameter location** for input models:

- `GetRoleQuery` describes query-string parameters.
- `PostRoleBody` and `PutRoleBody` describe JSON request bodies.
- `PostUserRoleBody` describes the nested user-role assignment request.
- Do not create an empty input model for a route without parameters.

Keep input validation in `controller/<resource>/schemas.py`, beside the resource's
`api.py`. Controllers map validated fields
once to explicit, typed application-service arguments. CRUD services and repository
ports do not need a second Command, Binding, Reference, or ListQuery object for
the same data. Repository filters are explicit and only omit `None`: combined
conditions use AND, and empty deletion conditions never execute a delete query.

Keep domain types when they carry real rules or a shared business contract, such
as scheduler validation, audit records, and request metadata. Do not add a generic
CRUD base class or a query language for ordinary field filtering.

#### Shared responses and pagination

Use `core.api_schema.Response` for ordinary success responses and
`PaginatedResponse(Response)` for paginated responses. Query models needing
pagination inherit `PaginatorSettings`; the existing defaults are page 1 and
page size 20. Business payload models remain separate from the shared envelope.

```python
from core.api_schema import PaginatedResponse, Response
from core.http import schema_response

schema_response(Response(), status=201)
schema_response(Response(results={"token": "access-token"}))
schema_response(PaginatedResponse(results=[], total_items=0, total_pages=0))
```

The JSON envelope uses `code`, `msg`, and `results`. Paginated responses keep
`total_items` and `total_pages` at the top level. Shared error models retain their
business codes and messages and use the same `results` field.

**Client migration:** replace reads of `response.result` with `response.results`.
Login now returns the token at `response.results.token`, not `response.token`:

```json
{"code": 0, "msg": "Success", "results": {"token": "access-token"}}
```

There is no legacy `result` alias. HTTP status codes and request payloads are
unchanged; HTTP 204 responses still have no response body on the wire. Internal
scheduler task-storage fields are not part of this HTTP envelope migration.

#### Complete CRUD example: permissions

The existing permission feature demonstrates the whole flow:

1. `controller/permissions/schemas.py` defines the HTTP inputs and payload models.
2. `controller/permissions/api.py` validates and maps inputs, invokes the service,
   and constructs responses. Its `register_routes` function declares the resource
   routes and receives the permission service and JWT dependency explicitly.
3. `controller/router.py` calls that resource registration function with the admin
   Blueprint. `app.create_app` calls the domain router; neither step looks up
   services through globals or `app.ctx`.
4. `services/permissions.py` applies existence checks and audit behavior through
   its dependency protocols. `repositories/permissions.py` performs ORM operations
   using the domain's `models.py`.

| Operation | Route | Input model | Response model |
| --- | --- | --- | --- |
| Read/filter | `GET /api/v1/admin/permissions` | `GetPermissionQuery(PaginatorSettings)` | `PaginatedResponse` |
| Create | `POST /api/v1/admin/permissions` | `PostPermissionBody` | `Response` |
| Update | `PUT /api/v1/admin/permissions` | `PutPermissionBody` | `Response` |
| Delete | `DELETE /api/v1/admin/permissions` | `DeletePermissionBody` | `Response` |

The controller maps the query to the service without creating another DTO:

```python
page = await self.permission_service.list_permissions(
    permission_id=query.id,
    permission_title=query.permission_title,
    page=query.page,
    page_size=query.page_size,
)
```

The service receives keyword-only parameters and calls its repository port with
the same explicit fields. The repository maps `permission_id` to the ORM's `id`;
it preserves name/ID combinations rather than silently preferring one filter.
Creation, updates, and deletion follow the same direct argument flow and keep
their existence checks and audit recording.

For an end-to-end example, use an admin token and the configured server address:

```bash
BASE_URL=http://localhost:8000
TOKEN="YOUR_ADMIN_ACCESS_TOKEN"

curl -X POST "$BASE_URL/api/v1/admin/permissions" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"permission_title":"reports:read"}'

curl "$BASE_URL/api/v1/admin/permissions?permission_title=reports:read&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Set this to the ID returned in results by the GET request.
PERMISSION_ID=123
curl -X PUT "$BASE_URL/api/v1/admin/permissions" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"id\":$PERMISSION_ID,\"permission_title\":\"reports:write\"}"

curl -X DELETE "$BASE_URL/api/v1/admin/permissions" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"id\":$PERMISSION_ID}"
```

The complete implementation is in the permission
[schemas](src/domains/identity_access/controller/permissions/schemas.py),
[controller](src/domains/identity_access/controller/permissions/api.py),
[router](src/domains/identity_access/controller/router.py),
[service](src/domains/identity_access/services/permissions.py), and
[repository](src/domains/identity_access/repositories/permissions.py).
When adding a resource, follow this flow rather than adding extra transport types
inside services or repositories. Add the resource's registration call to its domain
router and pass any new dependencies explicitly from `create_app`. Preserve
required, nullable, and omitted
field semantics explicitly: an optional type annotation alone does not make a
field optional in a request.

Schema names must be globally unique when used as OpenAPI components. The current
routes register input validation; automatic OpenAPI body/query/response schema
documentation is not yet configured. Naming a model does not register that
documentation by itself.

### Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

### License

Distributed under the MIT License. See `LICENSE` for more information.

### Contact

Github - [@Accec](https://github.com/Accec)

Project Link: [https://github.com/Accec/E-Start-Backend](https://github.com/Accec/E-Start-Backend)
