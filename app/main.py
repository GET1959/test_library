from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.authors.router import router as router_authors
from app.books.router import router as router_books
from app.auth.router import router as router_auth


app = FastAPI()


app.include_router(router_auth)
app.include_router(router_authors)
app.include_router(router_books)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    servers = []
    if app.root_path:
        servers = [{"url": app.root_path}]
    openapi_schema = get_openapi(
        title="Mobile Library Service",
        version="1.0.0",
        description="API for Mobile Library Service",
        routes=app.routes,
        servers=servers,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    public_paths = {"/auth/register", "/auth/login"}
    for path, methods in openapi_schema["paths"].items():
        if path in public_paths:
            continue
        for method in methods.values():
            if isinstance(method, dict):
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
