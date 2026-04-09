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
        v = "v3"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crazy Lister API - Docs</title>
  <link rel="stylesheet" type="text/css" href="/static/swagger-ui/swagger-ui.css?{v}">
  <style>
    html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
    *, *:before, *:after {{ box-sizing: inherit; }}
    body {{ margin: 0; background: #fafafa; }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="/static/swagger-ui/swagger-ui-bundle.js?{v}"></script>
  <script src="/static/swagger-ui/swagger-ui-standalone-preset.js?{v}"></script>
  <script>
    window.onload = function() {{
      try {{
        window.ui = SwaggerUIBundle({{
          url: "/openapi.json",
          dom_id: "#swagger-ui",
          deepLinking: true,
          presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
          ]},
          plugins: [SwaggerUIBundle.plugins.DownloadUrl],
          layout: "StandaloneLayout",
          docExpansion: "list",
          defaultModelsExpandDepth: 1,
          displayRequestDuration: true,
          filter: true
        }});
      }} catch(e) {{
        document.getElementById("swagger-ui").innerHTML = 
          "<div style='padding:40px;font-family:sans-serif;text-align:center;'>" +
          "<h2>Swagger UI Load Error</h2>" +
          "<p>" + e.message + "</p>" +
          "<p><a href='/redoc'>Try ReDoc &rarr;</a></p></div>";
      }}
    }};
  </script>
</body>
</html>"""

    @app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
    async def local_redoc():
        v = "v3"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crazy Lister API - ReDoc</title>
  <style>body {{ margin: 0; padding: 0; }}</style>
</head>
<body>
  <div id="redoc-container"></div>
  <script src="/static/redoc/redoc.standalone.js?{v}"></script>
  <script>
    window.onload = function() {{
      try {{
        Redoc.init("/openapi.json", {{
          expandResponses: "200,201",
          hideLoading: false,
          theme: {{ colors: {{ primary: {{ main: "#FF9900" }} }} }}
        }}, document.getElementById("redoc-container"));
      }} catch(e) {{
        document.getElementById("redoc-container").innerHTML = 
          "<div style='padding:40px;font-family:sans-serif;text-align:center;'>" +
          "<h2>ReDoc Load Error</h2>" +
          "<p>" + e.message + "</p>" +
          "<p><a href='/docs'>Try Swagger UI &rarr;</a></p></div>";
      }}
    }};
  </script>
</body>
</html>"""
