#!/usr/bin/env python3

import os
import argparse
import json
import mimetypes
from logger import get_logger
from mdparser import MarkdownParser
from sv_state import MdViewerState
from jinja2 import Environment, FileSystemLoader
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound

env = Environment(loader=FileSystemLoader("templates"))

def render_markdown_page(html: str) -> str:
    template = env.get_template("plain.html")
    return template.render(content=html)

logger = get_logger(__name__)

# ---------------------------------------------------------
# URL map
# ---------------------------------------------------------

url_map = Map([
    Rule("/", endpoint="index"),
    Rule("/static/<path:filename>", endpoint="static"),
    Rule("/v/<path:filename>", endpoint="view"),
    Rule("/m/<path:filename>", endpoint="mdplain"),
    Rule("/t/<path:filename>", endpoint="mdtext"),
    Rule("/api/tree", endpoint="dirtree"),
    Rule("/api/search", endpoint="search"),
])

# ---------------------------------------------------------
# Application
# ---------------------------------------------------------

class App:
    def __init__(self, config):
        self.url_map = url_map
        self.static_dir = "static"
        self.state = MdViewerState(config)

    # Dispatcher
    def dispatch(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(self, f"on_{endpoint}")
            return handler(request, **values)
        except NotFound:
            return Response("Not found", status=404, mimetype="text/plain")
        except HTTPException as e:
            return e

    # HTML
    def on_index(self, request):
        tree = self.state.get_tree()
        tree_md = env.get_template("tree.md").render(tree=tree)
        html = env.get_template("viewer.html").render(content=MarkdownParser.parse(tree_md))
        return Response(html, mimetype="text/html")

    def on_view(self, request, filename):
        md_html = self.state.get_content(filename)
        html = env.get_template("viewer.html").render(content=md_html)
        return Response(html, mimetype="text/html")

    # JSON
    def on_dirtree(self, request):
        tree = self.state.get_tree()
        return Response(json.dumps(tree), mimetype="application/json")
    
    def on_search(self, request):
        # Access query parameters
        query = request.args.get("query", None)  # default if missing
        result = self.state.search(query)
        return Response(json.dumps(result), mimetype="application/json")

    # Plain markdown
    def on_mdplain(self, request, filename):
        md_html = self.state.get_content(filename)
        html = env.get_template("plain.html").render(content=md_html)
        return Response(html, mimetype="text/html")

    # Plain markdown
    def on_mdtext(self, request, filename):
        raw_text = self.state.get_content(filename,raw=True)
        return Response(raw_text, mimetype="text/plain")

    # Static file
    def on_static(self, request, filename):
        path = os.path.join(self.static_dir, filename)
        if not os.path.isfile(path):
            return Response("Not found", status=404, mimetype="text/plain")
        
        with open(path, "rb") as f:
            data = f.read()
        
        # Guess MIME type
        mimetype, _ = mimetypes.guess_type(path)
        if not mimetype:
            mimetype = "application/octet-stream"
        
        return Response(data, mimetype=mimetype)

    # WSGI wrapper
    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request)
        return response(environ, start_response)

    # Callable wrapper
    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


# ---------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Markdown viewer")
    parser.add_argument("--dir", "-d", required=True, help="Directory to serve")
    parser.add_argument("--port", "-p", type=int,default=5000, help="Port to serve on")
    parser.add_argument("--host", "-H", default="localhost", help="Host to bind to")
    args = parser.parse_args()
    app = App(config={'dir':args.dir})
    run_simple(args.host, args.port, app, use_reloader=True)

if __name__ == "__main__":
    main()
