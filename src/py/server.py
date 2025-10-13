#!/usr/bin/python3

import os
import argparse
import json
from logger import get_logger
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse, parse_qs
from sv_state import MdViewerState

logger = get_logger(__name__)

class MdViewerServer(HTTPServer):
    """Custom HTTP server for Markdown Viewer."""
    def __init__(self, server_address, RequestHandlerClass, config: dict):
        super().__init__(server_address, RequestHandlerClass)
        self.config = config
        self.state = MdViewerState(config)

class MdViewerHandler(SimpleHTTPRequestHandler):
    """Request handler for Markdown Viewer."""

    # suppress default logging
    def log_message(self, format, *args):
        pass  

    # client disconnected early — just ignore it
    def handle(self):
        try:
            super().handle()
        except BrokenPipeError:
            pass  

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)
        logger.debug(f"GET: {path}, query: {query}")

        if path.startswith("/static/"):
            return self._serve_static(path)
        if path.startswith("/render/") or path == "/":
            return self._serve_index()
        if path == "/api/tree":
            return self._send_json(self.server.state.get_tree())
        if path == "/api/search":
            return self._handle_search(query)
        if path.startswith("/raw/"):
            return self._serve_content(path, raw=True)
        if path.startswith("/plain/"):
            return self._serve_content(path, raw=False)

        return self._send_error()

    def _serve_static(self, path: str):
        static_path = os.path.join("static", path[len("/static/"):])
        if os.path.isfile(static_path):
            self.path = "/" + static_path
            return super().do_GET()
        return self._send_error()

    def _serve_index(self):
        # Refresh state on explicit page request, not on every GET
        self.server.state.refresh()
        self.path = "/index.html"
        return super().do_GET()

    def _handle_search(self, query: dict):
        search_query = query.get("query", [None])[0]
        if not search_query:
            return self._send_error(400, "Missing 'query' parameter")
        return self._send_json(self.server.state.search(search_query))

    def _serve_content(self, path: str, raw: bool):
        # Handles both /raw/ and /plain/
        prefix = "/raw/" if raw else "/plain/"
        name = path[len(prefix):]
        name = unquote(name)  # Decode URL-encoded characters
        try:
            content = self.server.state.get_content(name, raw=raw)
            if raw:
                return self._send_plaintext(content)
            else:
                return self._send_html(content)
        except Exception as e:
            logger.error(f"Error serving content '{name}': {e}")
            return self._send_error()

    def _send_response(self, content: bytes, content_type: str, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        try:
            self.wfile.write(content)
        except BrokenPipeError:
            logger.warning("Client disconnected before response could complete")

    def _send_plaintext(self, content: str, code: int = 200):
        self._send_response(content.encode("utf-8"), "text/plain; charset=utf-8", code)

    def _send_json(self, data, code: int = 200):
        response_bytes = json.dumps(data).encode("utf-8")
        self._send_response(response_bytes, "application/json", code)

    def _send_html(self, content: str, code: int = 200):
        self._send_response(content.encode("utf-8"), "text/html", code)

    def _send_error(self, code: int = 404, message: str = "Not found"):
        if self.path.startswith("/api/"):
            self._send_json({"error": message}, code)
        else:
            self._send_plaintext(message, code)

def main():
    parser = argparse.ArgumentParser(description="Markdown viewer")
    parser.add_argument("--dir", required=True, help="Directory to serve")
    parser.add_argument("--port", default="5000", help="Port to serve on")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--precache", action="store_true", help="Pre-cache the contents of the directory")
    args = parser.parse_args()

    config = {}
    config["dir"] = args.dir
    config["precache"] = args.precache
    logger.debug(f"Config: {config}")

    server = MdViewerServer((args.host, int(args.port)), MdViewerHandler, config)
    logger.info(f"Serving on http://{args.host}:{args.port}/")
    server.serve_forever()

if __name__ == '__main__':
    main()
