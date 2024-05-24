import click
import random
import string
from tortoise import Tortoise, run_async
import datetime

import config

from utils.response import UserExistError

from models import User, Log, Role
from modules.encryptor import hash_password, generate_openid

Config = config.Config()

@click.group()
def cli():
    """Command Line Interface for E-Starter"""
    tortoise_config = {
            'connections': {
                'default': {
                    'engine': 'tortoise.backends.mysql',
                    'credentials': {
                            'host': Config.MysqlHost,
                            'port': Config.MysqlPort,
                            'user': Config.MysqlUsername,
                            'password': Config.MysqlPassword,
                            'database': Config.MysqlDatabaseName,
                        "maxsize":"15",
                        "minsize":"5"
                    }
                },
            },
            'apps': {
                Config.APP: {
                    'models': ["models"],
                    'default_connection': 'default',
                }
            },
            'use_tz': True,
        }
    
    run_async(Tortoise.init(
            config = tortoise_config,
        ))
    
@cli.command("init_database")
def init_database():
    async def init_database():
        await Tortoise.generate_schemas(safe=True)
        click.echo("Database initialized successfully.")

        if await Role.exists(role_name="Admin"):
            click.echo("Role: Admin is exist.")
        else:
            await Role.create(role_name="Admin")
            click.echo("Role: Admin created.")
        
        if await Role.exists(role_name="User"):
            click.echo("Role: User is exist.")
        else:
            await Role.create(role_name="Admin")
            click.echo("Role: User created.")

        if await Role.exists(role_name="Blacklist"):
            click.echo("Role: Blacklist is exist.")
        else:
            await Role.create(role_name="Admin")
            click.echo("Role: Blacklist created.")

    run_async(init_database())

@cli.command("create_admin")
@click.option("--username", default=None, show_default="Default is admin (if none provided)", help="The username of the new user.")
@click.option("--password", default=None, show_default="Random if none provided", help="The password of the new user.")
def create_admin(username, password):
    async def create_admin(username, password):
        if not username:
            username = "admin"
        if not password:
            password = "".join(random.choices(string.ascii_letters + string.digits, k=12))

        if await User.exists(account=username):
            click.echo(UserExistError.msg)
            return
        
        open_id = generate_openid(username, password, str(datetime.datetime.now(datetime.UTC).timestamp() * 1000))
        hashed_password = hash_password(password)

        new_user = User(account=username, password=hashed_password, open_id=open_id)
        await new_user.save()

        role = await Role.get(role_name="Admin")
        await new_user.roles.add(role)

        click.echo(f"Admin created [account: {username} - password: {password}].")

    run_async(create_admin(username, password))

    

if __name__ == "__main__":
    cli()
