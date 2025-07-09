# collector/ssh_manager.py
import paramiko
import time
import re
import os

class OntMonitor:
    """Manages the SSH connection and command execution on the device."""
    def __init__(self, host, port, username, password, timeout=10):
        self.host, self.port, self.username, self.password, self.timeout = host, port, username, password, timeout
        self.client, self.shell = None, None
        self.ansi_escape_pattern = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')

    def connect(self):
        if self.client: return
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f"Connecting to {self.host}:{self.port}...")
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password, timeout=self.timeout)
            self.shell = self.client.invoke_shell()
            time.sleep(1)
            if self.shell.recv_ready(): self.shell.recv(65535)
            print("Successfully connected to the router.")
        except Exception as e:
            print(f"Error connecting to SSH: {e}")
            self.close()
            raise

    def close(self):
        if self.client:
            self.client.close()
            self.client, self.shell = None, None
            print("SSH connection closed.")

    def run_command(self, command, wait=3):
        if not self.shell: raise Exception("SSH shell not connected.")
        print(f"Running command: {command}")
        self.shell.send(command + "\n")
        time.sleep(wait)
        output = ""
        while self.shell.recv_ready():
            output += self.shell.recv(65535).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        cleaned_output = self.ansi_escape_pattern.sub('', output)
        return cleaned_output.replace('\x07', '')

def load_ssh_config(host_alias):
    ssh_config_path = os.path.expanduser("~/.ssh/config")
    config = paramiko.SSHConfig()
    with open(ssh_config_path) as f: config.parse(f)
    host_config = config.lookup(host_alias)
    return host_config.get('hostname'), int(host_config.get('port', 22)), host_config.get('user')