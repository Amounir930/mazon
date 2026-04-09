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
  <link rel="stylesheet" type="text/css" href="/static/swagger-ui/swagger-ui.css">
  <style>
    html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #fafafa; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="/static/swagger-ui/swagger-ui-bundle.js"></script>
  <script src="/static/swagger-ui/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      try {
        window.ui = SwaggerUIBundle({
          url: "/openapi.json",
          dom_id: "#swagger-ui",
          deepLinking: true,
          presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
          ],
          plugins: [
            SwaggerUIBundle.plugins.DownloadUrl
          ],
          layout: "StandaloneLayout",
          docExpansion: "list",
          defaultModelsExpandDepth: 1,
          displayRequestDuration: true,
          filter: true,
          onComplete: function() {
            console.log("Swagger UI loaded successfully");
          },
          onError: function(err) {
            console.error("Swagger UI Error:", err);
          }
        });
      } catch(e) {
        document.getElementById("swagger-ui").innerHTML = 
          "<div style='padding:20px;font-family:sans-serif;'>" +
          "<h2>Error loading Swagger UI</h2>" +
          "<p>" + e.message + "</p>" +
          "<p>Try <a href='/redoc'>ReDoc</a> instead.</p></div>";
      }
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
  <style>
    body { margin: 0; padding: 0; }
  </style>
</head>
<body>
  <div id="redoc-container"></div>
  <script src="/static/redoc/redoc.standalone.js"></script>
  <script>
    window.onload = function() {
      try {
        Redoc.init("/openapi.json", {
          expandResponses: "200,201",
          hideLoading: false,
          theme: {
            colors: {
              primary: { main: "#FF9900" }
            }
          }
        }, document.getElementById("redoc-container"));
      } catch(e) {
        document.getElementById("redoc-container").innerHTML = 
          "<div style='padding:20px;font-family:sans-serif;'>" +
          "<h2>Error loading ReDoc</h2>" +
          "<p>" + e.message + "</p>" +
          "<p>Try <a href='/docs'>Swagger UI</a> instead.</p></div>";
      }
    };
  </script>
</body>
</html>"""
