# main.py
import sys
import time
import schedule
from pathlib import Path
from datetime import datetime

# Import from our custom modules
import config
import parsers
from ssh_manager import OntMonitor, load_ssh_config

def cleanup_old_files():
    """Finds and deletes files in the data directory older than the configured retention period."""
    print("--- Running Cleanup Job ---")
    try:
        retention_str = config.CLEANUP_OLDER_THAN
        value = int(retention_str[:-1])
        unit = retention_str[-1].lower()

        command = ["find", config.CLEAN_DATA_DIR, "-type", "f", "-name", "*.txt"]

        if unit == 'd':
            command.extend(["-mtime", f"+{value}"])
        elif unit == 'h':
            command.extend(["-mmin", f"+{value * 60}"])
        elif unit == 'm':
            command.extend(["-mmin", f"+{value}"])
        else:
            print(f"Warning: Invalid cleanup unit '{unit}'. Cleanup skipped.")
            return
            
        command.append("-delete")

        subprocess.run(command, check=True)
        print(f"Successfully deleted files older than {retention_str}.")
    except Exception as e:
        print(f"Cleanup job failed: {e}")

def process_command(command, ont, output_dir):
    """Runs a command, parses it, and saves the clean output."""
    try:
        raw_output = ont.run_command(command)
        command_prefix = command.replace(' ', '_')
        lines = raw_output.splitlines()

        # Filter content
        content_lines = [line for i, line in enumerate(lines) if i > 0 and not line.lower().startswith('success!')]

        # Dispatcher dictionary to map commands to parser functions
        parser_map = {
            "display cpu info": parsers.parse_cpu_info,
            "wap top": parsers.parse_wap_top,
            "display sfwd drop statistics": parsers.parse_sfwd_drop,
            "display lanport workmode": parsers.parse_lanport_workmode,
            "display dhcp server user all": parsers.parse_dhcp_server,
            "display wifi associate": parsers.parse_wifi_associate,
            "display port statistics portid": parsers.parse_key_value,
            "display deviceinfo": lambda l, p: parsers.parse_key_value(l, p, separator='='),
            "display waninfo all detail": parsers.parse_key_value,
            "display wifi information": parsers.parse_key_value,
        }
        
        # Find the correct parser
        output_lines = []
        for key, parser_func in parser_map.items():
            if key in command:
                output_lines = parser_func(content_lines, command_prefix)
                break
        else: # If no specific parser is found, use the default
            output_lines = parsers.parse_key_value(content_lines, command_prefix)

        # Save the final, clean file
        if output_lines:
            command_output_dir = Path(output_dir) / command_prefix
            command_output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y_%m_%d__%H_%M")
            filename = f"{command_prefix}_{timestamp}.txt"
            filepath = command_output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f_out:
                f_out.write('\n'.join(output_lines))
            print(f"Successfully processed and saved '{command}' to {filepath}")
        else:
            print(f"Warning: No parsable data generated for command '{command}'.")

    except Exception as e:
        print(f"Failed to process command '{command}': {e}")

def run_job(commands, ont, output_dir):
    """Function to be scheduled. Runs a list of commands."""
    print(f"\n--- Running Job: {datetime.now()} ---")
    try:
        ont.connect()
        for cmd in commands:
            process_command(cmd, ont, output_dir)
    except Exception as e:
        print(f"Job failed: {e}")
    
def main():
    """Main function to schedule and run data collection and cleanup jobs."""
    if not config.PASSWORD:
        print("Error: ONT_PASSWORD environment variable not set. Please create a .env file.")
        sys.exit(1)

    try:
        host, port, username = load_ssh_config(config.SSH_HOST_ALIAS)
    except Exception as e:
        print(f"Failed to load SSH config for '{config.SSH_HOST_ALIAS}': {e}")
        sys.exit(1)

    ont_monitor = OntMonitor(host, port, username, config.PASSWORD)
    
    # Schedule collection jobs
    schedule.every(1).minutes.do(run_job, commands=config.COMMANDS_1_MIN, ont=ont_monitor)
    schedule.every(5).minutes.do(run_job, commands=config.COMMANDS_5_MIN, ont=ont_monitor)
    
    # Schedule the cleanup job dynamically
    try:
        freq_val = int(config.CLEANUP_FREQUENCY[:-1])
        freq_unit = config.CLEANUP_FREQUENCY[-1].lower()

        scheduler = schedule.every(freq_val)

        if freq_unit == 'm':
            scheduler.minutes.do(cleanup_old_files)
        elif freq_unit == 'h':
            scheduler.hours.do(cleanup_old_files)
        elif freq_unit == 'd':
            scheduler.days.at("03:00").do(cleanup_old_files) # Run daily jobs at a set time
        else:
            raise ValueError(f"Invalid frequency unit: {freq_unit}")
        
        print(f"Cleanup job scheduled to run every {config.CLEANUP_FREQUENCY}.")

    except Exception as e:
        print(f"Error scheduling cleanup job: {e}. Defaulting to every 1 day.")
        schedule.every(1).day.at("03:00").do(cleanup_old_files)


    print("--- Unified Collector & Parser Started ---")
    
    # Initial run
    run_job(config.COMMANDS_1_MIN, ont_monitor)
    run_job(config.COMMANDS_5_MIN, ont_monitor)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        ont_monitor.close()

if __name__ == "__main__":
    main()
