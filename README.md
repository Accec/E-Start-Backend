# E-Starter

E-Starter is a simple and easy-to-use backend framework designed for small to medium-sized projects. It provides a robust starting point for developers looking to jumpstart their application development without dealing with complex configurations.

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
   Config keys use `snake_case` consistently, for example `jwt_secret_key`, `redis_url`, `mysql_database_name`.
   ```bash
   vi <CONFIG_NAME>.yaml
   ```
5. Navigate back to the project root:
   ```bash
   cd ../../..
   ```
6. Open `src/.env` with a text editor (like `vi`):
   ```bash
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

Migration config lives in `pyproject.toml`, and generated files are stored under `migrations/demo/`.
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

The project now follows a DDD-oriented layout:

```text
src/
  app/bootstrap/         # application assembly and startup wiring
  core/                  # shared conventions, config, constants, HTTP helpers
  infra/                 # Redis, scheduler, security, logging and other adapters
  domains/
    identity_access/     # users, roles, permissions, endpoints
      application/
      domain/
      infrastructure/
      presentation/
    audit/               # audit log use cases and persistence
      application/
      domain/
      infrastructure/
      presentation/
    operations/          # operational jobs and scheduler management
      application/
      domain/
      infrastructure/
      presentation/
  middleware/            # request-scoped cross-cutting behavior
  scripts/ops/           # operator CLI and manual scripts
  tests/                 # structural and regression checks
migrations/              # Aerich migration root
  demo/                  # versioned migration files for the demo app
docs/legacy/             # notes about retired pre-migration artifacts
```

### Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

### License

Distributed under the MIT License. See `LICENSE` for more information.

### Contact

Github - [@Accec](https://github.com/Accec)

Project Link: [https://github.com/Accec/E-Start-Backend](https://github.com/Accec/E-Start-Backend)
