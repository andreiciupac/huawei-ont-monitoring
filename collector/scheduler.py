# collector/scheduler.py
import time
import schedule
import subprocess
import config
from ssh_manager import OntMonitor, load_ssh_config
from main import process_command

def cleanup_old_files():
    print("--- Running Cleanup Job ---")
    try:
        retention_str = config.CLEANUP_OLDER_THAN
        value = int(retention_str[:-1])
        unit = retention_str[-1].lower()
        command = ["find", config.CLEAN_DATA_DIR, "-type", "f", "-name", "*.txt"]
        if unit == 'd': command.extend(["-mtime", f"+{value}"])
        elif unit == 'h': command.extend(["-mmin", f"+{value * 60}"])
        elif unit == 'm': command.extend(["-mmin", f"+{value}"])
        else:
            print(f"Warning: Invalid cleanup unit '{unit}'. Cleanup skipped.")
            return
        command.append("-delete")
        subprocess.run(command, check=True)
        print(f"Successfully deleted files older than {retention_str}.")
    except Exception as e:
        print(f"Cleanup job failed: {e}")

def run_job(commands, ont):
    print(f"\n--- Running Job: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    try:
        ont.connect()
        for cmd in commands:
            process_command(cmd, ont)
    except Exception as e:
        print(f"Job failed: {e}")

def start():
    try:
        host, port, username = load_ssh_config(config.SSH_HOST_ALIAS)
    except Exception as e:
        print(f"Failed to load SSH config for '{config.SSH_HOST_ALIAS}': {e}")
        return
    ont_monitor = OntMonitor(host, port, username, config.PASSWORD)
    schedule.every(30).seconds.do(run_job, commands=config.COMMANDS_30_SEC, ont=ont_monitor)
    schedule.every(5).minutes.do(run_job, commands=config.COMMANDS_5_MIN, ont=ont_monitor)
    try:
        freq_val = int(config.CLEANUP_FREQUENCY[:-1])
        freq_unit = config.CLEANUP_FREQUENCY[-1].lower()
        scheduler = schedule.every(freq_val)
        if freq_unit == 'm': scheduler.minutes.do(cleanup_old_files)
        elif freq_unit == 'h': scheduler.hours.do(cleanup_old_files)
        elif freq_unit == 'd': scheduler.days.at("03:00").do(cleanup_old_files)
        else: raise ValueError(f"Invalid frequency unit: {freq_unit}")
        print(f"Cleanup job scheduled to run every {config.CLEANUP_FREQUENCY}.")
    except Exception as e:
        print(f"Error scheduling cleanup job: {e}. Defaulting to every 1 day.")
        schedule.every(1).day.at("03:00").do(cleanup_old_files)
    print("--- Unified Collector & Parser Started ---")
    run_job(config.COMMANDS_30_SEC, ont_monitor)
    run_job(config.COMMANDS_5_MIN, ont_monitor)

    cleanup_old_files()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        ont_monitor.close()