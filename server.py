import http.server
import os
import subprocess
import threading
import json

PORT = 8888
BASE_DIR = "/home/perizat/hacknu-growth"

class Handler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/refresh":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "running"}).encode())

            def run():
                subprocess.run([
                    "python3",
                    f"{BASE_DIR}/generate_report.py"
                ])
                subprocess.run([
                    "python3",
                    f"{BASE_DIR}/build_dashboard.py"
                ])
            threading.Thread(target=run).start()

        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass

os.chdir(BASE_DIR)
print(f"Server running at http://localhost:{PORT}")
print(f"Open: http://localhost:{PORT}/dashboard.html")
http.server.HTTPServer(("", PORT), Handler).serve_forever()
