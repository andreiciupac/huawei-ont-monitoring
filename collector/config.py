# collector/config.py
import os

# --- Configuration loaded from environment variables ---

# The alias for your router from your ~/.ssh/config file
SSH_HOST_ALIAS = os.getenv("SSH_HOST_ALIAS", "ont.home")

# The SSH password for your router
PASSWORD = os.getenv("ONT_PASSWORD")

# The final output directory that the Prometheus exporter will read from.
# This path is INSIDE the container. Docker will map it to the host.
CLEAN_DATA_DIR = '/data'

# How long to keep the parsed data files. Loaded from environment.
# Format: '7d', '48h', etc. Defaults to 7 days.
CLEANUP_OLDER_THAN = os.getenv("CLEANUP_OLDER_THAN", "7d")

# How often to run the cleanup job. Defaults to every 1 day.
CLEANUP_FREQUENCY = os.getenv("CLEANUP_FREQUENCY", "1d")


# --- Command Scheduling ---
COMMANDS_30_SEC = [
    "display sfwd drop statistics",
    "display portstatistics portnum 1",
    "wap top",
]
COMMANDS_5_MIN = [
    "display lanport workmode",
    "display dhcp server user all",
    "display deviceinfo",
    "display wifi associate",
    "display wifi information",
    "display waninfo all detail"
]