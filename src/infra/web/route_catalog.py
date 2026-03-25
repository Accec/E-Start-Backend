class SanicRouteCatalog:
    def __init__(self, app_name: str):
        self.app_name = app_name

    def list_routes(self):
        import sanic

        server = sanic.Sanic.get_app(self.app_name)
        discovered = set()

        for route in server.router.groups.values():
            for method in route.methods:
                discovered.add((route.path, method))

        return [
            {"endpoint": endpoint, "method": method}
            for endpoint, method in sorted(discovered)
        ]
