class RemoveServerHeaderMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            headers = [(k, v) for (k, v) in headers if k.lower() != "server"]
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
