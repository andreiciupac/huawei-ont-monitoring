# collector/main.py
import sys
from pathlib import Path
from datetime import datetime

import config
import parsers
import scheduler # Import the new scheduler module

def process_command(command, ont):
    """Runs a command, parses it, and saves the clean output."""
    try:
        raw_output = ont.run_command(command)
        command_prefix = command.replace(' ', '_')
        lines = raw_output.splitlines()
        content_lines = [line for i, line in enumerate(lines) if i > 0 and not line.lower().startswith('success!')]
        
        parser_map = {
            "display cpu info": parsers.parse_cpu_info,
            "wap top": parsers.parse_wap_top,
            # ... (rest of the parser map from the previous version) ...
        }
        
        output_lines = []
        for key, parser_func in parser_map.items():
            if key in command:
                output_lines = parser_func(content_lines, command_prefix)
                break
        else:
            output_lines = parsers.parse_key_value(content_lines, command_prefix)

        if output_lines:
            command_output_dir = Path(config.CLEAN_DATA_DIR) / command_prefix
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

if __name__ == "__main__":
    if not config.PASSWORD:
        print("Error: ONT_PASSWORD environment variable not set. Please create a .env file.")
        sys.exit(1)
    
    # Start the main scheduling loop from the scheduler module
    scheduler.start()
