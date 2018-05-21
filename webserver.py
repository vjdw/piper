from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs

class HTTPServer_RequestHandler(BaseHTTPRequestHandler):
 
    menu = None
    mopidy = None

    # GET
    def do_GET(self):
        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        #self.mopidy.toggle_pause()

        query = urlsplit(self.path).query
        params = parse_qs(query)
        params_dict = {k: v[0] for k, v in params.items()}
        if 'i' in params_dict and params_dict['i'] == '0':
            active_menu = self.menu.items[0].child_menu
        else:
            active_menu = self.menu

        message = ["<p><a href=\"http://localhost:8081/?d=0&i={}&m={}&t={}\">{}</a></p>".format(i, x.method, x.target, x.text) for i,x in enumerate(active_menu.items)]
        message = "<html>{}<html>".format(''.join(message))
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

class WebServer:
    def __init__(self, menu, mopidy):
        HTTPServer_RequestHandler.menu = menu
        HTTPServer_RequestHandler.mopidy = mopidy

    def run(self):
        server = HTTPServer(('', 8081), HTTPServer_RequestHandler)
        server.serve_forever()