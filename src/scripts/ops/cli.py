import asyncio
import base64
import os
import secrets
import subprocess
import sys
from pathlib import Path

import click
from tortoise import Tortoise

from app.bootstrap.container import build_bootstrap
from app.bootstrap.database import build_tortoise_orm_config
from core.config import load_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AERICH_CONFIG_PATH = PROJECT_ROOT / "pyproject.toml"
MIGRATIONS_ROOT = PROJECT_ROOT / "migrations"


def get_migration_app_name():
    return load_config().app


def get_migration_app_dir():
    return MIGRATIONS_ROOT / get_migration_app_name()


@click.group()
def cli():
    """Command Line Interface for demo."""


def run_database_task(operation, *args, **kwargs):
    async def runner():
        await Tortoise.init(config=build_tortoise_orm_config())
        try:
            return await operation(*args, **kwargs)
        finally:
            await Tortoise.close_connections()

    # The operator CLI needs the coroutine result, so use asyncio.run instead
    # of tortoise.run_async, which is better suited to fire-and-forget helpers.
    return asyncio.run(runner())


def run_aerich_command(*args: str):
    if not AERICH_CONFIG_PATH.exists():
        raise click.ClickException(f"Aerich config file is missing: {AERICH_CONFIG_PATH}")

    env = dict(os.environ)
    src_path = str(PROJECT_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing_pythonpath else f"{src_path}{os.pathsep}{existing_pythonpath}"

    command = [
        sys.executable,
        "-m",
        "aerich",
        "-c",
        str(AERICH_CONFIG_PATH),
        "--app",
        get_migration_app_name(),
        *args,
    ]

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(
            "Aerich is not installed in the current interpreter. "
            "Install dependencies with `pip install -r src/requirements.txt`."
        ) from exc

    if result.stdout:
        click.echo(result.stdout, nl=False)
    if result.stderr:
        click.echo(result.stderr, err=True, nl=False)

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        if details:
            detail_lines = "\n".join(details.splitlines()[-12:])
            raise click.ClickException(
                f"Aerich command failed with exit code {result.returncode}.\n{detail_lines}"
            )
        raise click.ClickException(f"Aerich command failed with exit code {result.returncode}.")


def migration_files_exist():
    migration_app_dir = get_migration_app_dir()
    if not migration_app_dir.exists():
        return False

    return any(
        path.is_file() and path.suffix == ".py" and path.name != "__init__.py"
        for path in migration_app_dir.iterdir()
    )


async def seed_default_roles():
    service = build_bootstrap().identity_access.bootstrap_service
    return await service.ensure_default_roles()


async def check_database_connection():
    await Tortoise.init(config=build_tortoise_orm_config())
    try:
        connection = Tortoise.get_connection("default")
        await connection.execute_query("SELECT 1")
    finally:
        await Tortoise.close_connections()


def print_role_bootstrap_results(results):
    for result in results:
        action = "created" if result.created else "already exists"
        click.echo(f"Role {result.role_name} {action}.")


@cli.command("init_database")
def init_database():
    if migration_files_exist():
        run_aerich_command("upgrade")
    else:
        run_aerich_command("init-db")

    results = run_database_task(seed_default_roles)
    print_role_bootstrap_results(results)
    click.echo("Database initialized successfully.")


@cli.command("migration_init_db")
def migration_init_db():
    # Keep database bootstrap migration-driven only. Manual pre-SQL hooks create
    # an untracked schema history that drifts away from the committed migrations.
    run_aerich_command("init-db")


@cli.command("migration_init_migrations")
def migration_init_migrations():
    run_aerich_command("init-migrations")


@cli.command("migration_heads")
def migration_heads():
    run_aerich_command("heads")


@cli.command("migration_doctor")
def migration_doctor():
    config = load_config()

    try:
        asyncio.run(check_database_connection())
    except Exception as exc:
        message = [
            "Database connection check failed.",
            f"Target: mysql://{config.mysql_username}@{config.mysql_host}:{config.mysql_port}/{config.mysql_database_name}",
            f"Reason: {exc}",
            "Fix the database credentials or make the database reachable before running Aerich commands.",
        ]
        raise click.ClickException("\n".join(message)) from exc

    click.echo(
        "Database connection is ready for migrations: "
        f"mysql://{config.mysql_username}@{config.mysql_host}:{config.mysql_port}/{config.mysql_database_name}"
    )


@cli.command("migration_history")
def migration_history():
    run_aerich_command("history")


@cli.command("migration_migrate")
@click.option("--name", default="update", show_default=True, help="Human-readable migration name.")
@click.option("--empty", is_flag=True, help="Create an empty migration file.")
@click.option("--offline", is_flag=True, help="Generate SQL diff without connecting to the database.")
@click.option("--no-input", is_flag=True, help="Do not ask for interactive confirmation.")
def migration_migrate(name, empty, offline, no_input):
    command = ["migrate", "--name", name]
    if empty:
        command.append("--empty")
    if offline:
        command.append("--offline")
    if no_input:
        command.append("--no-input")
    run_aerich_command(*command)


@cli.command("migration_upgrade")
@click.option("--fake", is_flag=True, help="Mark migrations as applied without running SQL.")
def migration_upgrade(fake):
    command = ["upgrade"]
    if fake:
        command.append("--fake")
    run_aerich_command(*command)


@cli.command("migration_downgrade")
@click.option("--version", type=int, default=None, help="Target migration version. Defaults to the latest one.")
@click.option("--delete", is_flag=True, help="Delete the migration file after rollback.")
@click.option("--fake", is_flag=True, help="Mark migration as rolled back without running SQL.")
@click.option("--yes", is_flag=True, help="Skip interactive confirmation.")
def migration_downgrade(version, delete, fake, yes):
    command = ["downgrade"]
    if version is not None:
        command.extend(["--version", str(version)])
    if delete:
        command.append("--delete")
    if fake:
        command.append("--fake")
    if yes:
        command.append("--yes")
    run_aerich_command(*command)


@cli.command("seed_identity_access")
def seed_identity_access():
    results = run_database_task(seed_default_roles)
    print_role_bootstrap_results(results)


@cli.command("create_admin")
@click.option("--username", default=None, show_default="Default is admin (if none provided)", help="The username of the new user.")
@click.option("--password", default=None, show_default="Random if none provided", help="The password of the new user.")
def create_admin(username, password):
    async def create_admin_user(username, password):
        service = build_bootstrap().identity_access.bootstrap_service
        return await service.create_admin(username=username, password=password)

    result = run_database_task(create_admin_user, username, password)
    if result.created:
        click.echo(f"Admin created [account: {result.account} - password: {result.password}].")
        return

    if result.role_assigned:
        click.echo(f"Admin role assigned to existing user [{result.account}].")
        return

    click.echo(f"Admin user [{result.account}] already exists.")


@cli.command("get_secret", help="Generate secret token for JWT or Nginx.")
@click.option("--length", default=4096, show_default="Default is 4096 (if none provided)", help="The length of the token.")
def get_secret(length: int):
    token = base64.b64encode(secrets.token_bytes(length)).decode()
    click.echo(f"{token}")


if __name__ == "__main__":
    cli()
