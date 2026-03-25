import argparse
import asyncio


def cli():
    parser = argparse.ArgumentParser(description="Backend Entrypoint")
    parser.add_argument(
        "command",
        nargs="?",
        default="server",
        help="server | scheduler | <ops command>",
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.command == "server":
        from app.bootstrap import start_http_server

        start_http_server()
        return

    if args.command == "scheduler":
        from app.bootstrap import start_scheduler

        asyncio.run(start_scheduler())
        return

    from scripts.ops import cli as ops_cli

    ops_cli.main(args=[args.command, *args.args], prog_name="python src/main.py")


if __name__ == "__main__":
    cli()
