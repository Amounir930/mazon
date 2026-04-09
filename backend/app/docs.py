"""
Serve API documentation with 100% local assets - zero CDN dependency.
All JS/CSS files are served from /static/ directory inside the container.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path


STATIC_DIR = Path(__file__).parent.parent / "static"


def register_docs_routes(app: FastAPI):
    """Mount static files and register local documentation endpoints"""

    # Mount static files for local asset serving
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
    async def local_swagger():
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crazy Lister API - Docs</title>
  <link rel="stylesheet" href="/static/swagger-ui/swagger-ui.css">
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="/static/swagger-ui/swagger-ui-bundle.js"></script>
  <script src="/static/swagger-ui/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      window.ui = SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout"
      });
    };
  </script>
</body>
</html>"""

    @app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
    async def local_redoc():
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crazy Lister API - ReDoc</title>
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
  <redoc spec-url="/openapi.json"></redoc>
  <script src="/static/redoc/redoc.standalone.js"></script>
</body>
</html>"""
