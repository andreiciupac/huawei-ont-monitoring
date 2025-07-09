# collector/main.py
import sys
import re
from pathlib import Path
from datetime import datetime
import config
import parsers
import scheduler
from ssh_manager import OntMonitor

def process_command(command: str, ont: OntMonitor):
    try:
        raw_output = ont.run_command(command)
        command_prefix = command.replace(' ', '_')
        lines = raw_output.splitlines()
        content_lines = [line for i, line in enumerate(lines) if i > 0 and not line.lower().startswith('success!')]
        port_match = re.search(r'portnum_(\d+)', command_prefix)
        port_label = port_match.group(1) if port_match else 'unknown'
        base_labels = {'command': command_prefix, 'port': port_label}
        
        parser_map = {
            "display deviceinfo": parsers.parse_deviceinfo,
            "display waninfo all detail": parsers.parse_waninfo_all_detail,
            "display wifi information": parsers.parse_wifi_information,
            "display dhcp server user all": parsers.parse_dhcp_server,
            "wap top": parsers.parse_wap_top,
            "display sfwd drop statistics": parsers.parse_sfwd_drop,
            "display lanport workmode": parsers.parse_lanport_workmode,
            "display wifi associate": parsers.parse_wifi_associate,
            "display portstatistics portnum 1": parsers.parse_key_value,
        }
        
        output_lines = []
        for key, parser_func in parser_map.items():
            if key in command:
                output_lines = parser_func(content_lines, command_prefix, base_labels)
                break
        else:
            output_lines = parsers.parse_key_value(content_lines, command_prefix, base_labels)

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
    scheduler.start()
