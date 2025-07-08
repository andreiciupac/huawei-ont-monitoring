# exporter/exporter.py
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

DATA_DIR = '/data' 
PORT = 8000

def find_latest_file(directory):
    try:
        files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]
        if not files: return None
        return max(files, key=os.path.getmtime)
    except FileNotFoundError:
        return None

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            all_metrics = []
            if not os.path.isdir(DATA_DIR):
                print(f"Error: Data directory '{DATA_DIR}' not found.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Data directory not found.")
                return
            for command_name in os.listdir(DATA_DIR):
                command_path = os.path.join(DATA_DIR, command_name)
                if os.path.isdir(command_path):
                    latest_file = find_latest_file(command_path)
                    if latest_file:
                        try:
                            with open(latest_file, 'r', encoding='utf-8') as f:
                                all_metrics.append(f.read())
                        except Exception as e:
                            print(f"Error reading file {latest_file}: {e}")
            output = "\n".join(all_metrics).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(output)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        return

def start_server(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MetricsHandler)
    print(f"Exporter started on http://localhost:{port}/metrics")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nExporter shutting down.")
        httpd.server_close()

if __name__ == '__main__':
    start_server(PORT)