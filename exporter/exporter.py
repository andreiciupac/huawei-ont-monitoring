import os
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import CollectorRegistry, Gauge, generate_latest

# --- Configuration ---
# The directory where your 'clean_data' subdirectories are located.
# This can be changed to an absolute path, e.g., '/home/user/device_logs/clean_data'
DATA_DIR = '/data'
# The port the exporter will listen on.
PORT = 8000

def find_latest_file(directory):
    """Finds the most recent file in a directory based on its filename."""
    try:
        files = [f for f in os.listdir(directory) if f.endswith('.txt') and os.path.isfile(os.path.join(directory, f))]
        if not files:
            return None
        # The last file when sorted alphabetically will be the most recent based on YYYY_MM_DD__HH_MM format.
        return os.path.join(directory, sorted(files)[-1])
    except FileNotFoundError:
        return None

def update_metrics(registry):
    """
    Scans the data directory, finds the latest file in each subdirectory,
    and populates a Prometheus registry with the metrics.
    """
    print("Collecting metrics from log files...")
    
    # A dictionary to hold our Gauge metrics for this scrape.
    gauges = {}
    
    if not os.path.isdir(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found.")
        return

    # Iterate over each command's subdirectory (e.g., 'display_portstatistics_portnum_1')
    for command_name in os.listdir(DATA_DIR):
        command_path = os.path.join(DATA_DIR, command_name)

        if os.path.isdir(command_path):
            latest_file = find_latest_file(command_path)

            if latest_file:
                print(f"  Parsing latest file for '{command_name}': {os.path.basename(latest_file)}")
                
                # --- Extract labels from the command name ---
                port_match = re.search(r'portnum_(\d+)', command_name)
                port_label = port_match.group(1) if port_match else 'unknown'
                
                labels = {'command': command_name, 'port': port_label}

                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '=' not in line:
                                continue
                            
                            key, value_str = line.strip().split('=', 1)
                            
                            # --- Sanitize the metric name ---
                            metric_name = key.replace(f"{command_name}_", "", 1).replace('-', '_')
                            metric_name = f"port_{metric_name}"

                            try:
                                value = float(value_str)
                            except ValueError:
                                continue

                            # --- Create Gauge if it doesn't exist for this scrape ---
                            if metric_name not in gauges:
                                gauges[metric_name] = Gauge(
                                    metric_name,
                                    f'Statistic for {metric_name}',
                                    labels.keys(),
                                    registry=registry
                                )
                            
                            # Set the value for the specific set of labels
                            gauges[metric_name].labels(**labels).set(value)

                except Exception as e:
                    print(f"Error parsing file {latest_file}: {e}")

class MetricsHandler(BaseHTTPRequestHandler):
    """A custom HTTP handler to serve Prometheus metrics."""
    def do_GET(self):
        if self.path == '/metrics':
            # Create a fresh registry for each request to avoid stale metrics.
            registry = CollectorRegistry()
            update_metrics(registry)
            
            # Generate the metrics output.
            output = generate_latest(registry)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(output)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        """Suppress log messages for each GET request to keep the console clean."""
        return

def start_server(port):
    """Starts the Prometheus exporter HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MetricsHandler)
    print(f"Exporter started on http://localhost:{port}/metrics")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nExporter shutting down.")
        httpd.server_close()

if __name__ == '__main__':
    # Make sure to configure the DATA_DIR variable at the top of the script.
    start_server(PORT)
