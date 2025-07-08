# config.py

# The alias for your router from your ~/.ssh/config file
SSH_HOST_ALIAS = os.getenv("SSH_HOST_ALIAS", "ont")

# The SSH password for your router
PASSWORD = os.getenv("ONT_PASSWORD")

# The final output directory that the Prometheus exporter will read from.
# IMPORTANT: Use the absolute path to your clean_data directory.
CLEAN_DATA_DIR = '/data'

# How long to keep the parsed data files. Defaults to 7 days.
CLEANUP_OLDER_THAN = os.getenv("CLEANUP_OLDER_THAN", "7d")

# How often to run the cleanup job. Defaults to every 1 day.
CLEANUP_FREQUENCY = os.getenv("CLEANUP_FREQUENCY", "1d")

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