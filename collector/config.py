# config.py

# --- SSH and Path Configuration ---
SSH_HOST_ALIAS = "ont.home"
PASSWORD = "admin111"

# The final output directory that the Prometheus exporter will read from.
# IMPORTANT: Use the absolute path to your clean_data directory.
CLEAN_DATA_DIR = '/data'


# --- Command Scheduling ---

# Commands to be run every 1 minute
COMMANDS_1_MIN = [
    "display sfwd drop statistics",
    "display portstatistics portnum 1",
    "display port statistics portid 1",
    "wap top",
]

# Commands to be run every 5 minutes
COMMANDS_5_MIN = [
    "display lanport workmode",
    "display dhcp server user all",
    "display deviceinfo",
    "display cpu info",
    "display wifi associate",
    "display wifi information",
    "display waninfo all detail"
]