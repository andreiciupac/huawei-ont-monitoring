# parsers.py
import re

def parse_key_value(lines, command_prefix, separator=':'):
    output = []
    for line in lines:
        if separator not in line: continue
        parts = line.split(separator, 1)
        if len(parts) != 2: continue
        key, value = parts[0].strip(), parts[1].strip()
        try:
            float(value)
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).lower()
            output.append(f"{command_prefix}_{clean_key}={value}")
        except ValueError:
            continue
    return output

def parse_cpu_info(lines, command_prefix):
    output, cpu_data, processor_id = [], {}, None
    for line in lines:
        if not line.strip():
            if processor_id is not None and 'BogoMIPS' in cpu_data:
                output.append(f"{command_prefix}_bogomips{{processor=\"{processor_id}\"}}={cpu_data['BogoMIPS']}")
            cpu_data, processor_id = {}, None
            continue
        if ':' in line:
            key, value = [p.strip() for p in line.split(':', 1)]
            if key == 'processor': processor_id = value
            else: cpu_data[key] = value
    if processor_id is not None and 'BogoMIPS' in cpu_data:
        output.append(f"{command_prefix}_bogomips{{processor=\"{processor_id}\"}}={cpu_data['BogoMIPS']}")
    return output

def parse_wap_top(lines, command_prefix):
    output = []
    for line in lines:
        if line.startswith('Mem:'):
            parts = re.findall(r'(\d+)K\s+(\w+)', line)
            for value, key in parts: output.append(f"{command_prefix}_mem_{key}_kb={value}")
        if line.startswith('CPU:'):
            parts = re.findall(r'(\d+\.\d+)%\s+(\w+)', line)
            for value, key in parts: output.append(f"{command_prefix}_cpu_{key}_percent={value}")
    return output

def parse_sfwd_drop(lines, command_prefix):
    output = []
    for line in lines:
        if ':' in line and not line.strip().startswith('['):
            key, value = [p.strip() for p in line.split(':', 1)]
            output.append(f"{command_prefix}_{key}={value}")
    header_line, value_line = None, None
    for i, line in enumerate(lines):
        if 'bcast' in line and 'arp' in line:
            header_line = line.strip().split()
            if i + 1 < len(lines): value_line = lines[i+1].strip().split()
            break
    if header_line and value_line:
        for key, value in zip(header_line, value_line):
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).lower()
            output.append(f"{command_prefix}_protocol_{clean_key}={value}")
    return output

def parse_lanport_workmode(lines, command_prefix):
    output = []
    for line in lines:
        match = re.match(r'^\s*(\d+)\s+([\w\d]+)\s+([\w\s]+)\s*$', line)
        if match:
            index, name, mode_str = match.groups()
            output.append(f'{command_prefix}_info{{index="{index}",name="{name}",workmode="{mode_str.strip()}"}} 1')
    return output

def parse_dhcp_server(lines, command_prefix):
    output, total_users = [], 0
    for line in lines:
        if line.strip().startswith('Total:'):
            total_users = line.strip().split(':')[1].strip()
            continue
        match = re.match(r'^\s*(\d+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\s+([0-9a-f:]+)\s+(.*)$', line, re.I)
        if match:
            index, port, ip, hostname, mac, _ = match.groups()
            output.append(f'{command_prefix}_lease_info{{index="{index}",port="{port}",ip="{ip}",hostname="{hostname.strip()}",mac="{mac}"}} 1')
    if total_users: output.append(f'{command_prefix}_total_users={total_users}')
    return output

def parse_wifi_associate(lines, command_prefix):
    output, band = [], None
    for line in lines:
        if "2.4GHz" in line: band = "2.4GHz"
        elif "5GHz" in line: band = "5GHz"
        match = re.match(r'^([0-9A-F:]{17})\s+(\S+)\s+(\d+)\s+(\d+)M\s+(\d+)M.*$', line, re.I)
        if match and band:
            mac, ssid, time_sec, tx_rate, rx_rate = match.groups()
            mac_sanitized = mac.replace(':', '')
            output.append(f'{command_prefix}_uptime_seconds{{mac="{mac_sanitized}",ssid="{ssid}",band="{band}"}}={time_sec}')
            output.append(f'{command_prefix}_tx_rate_mbps{{mac="{mac_sanitized}",ssid="{ssid}",band="{band}"}}={tx_rate}')
            output.append(f'{command_prefix}_rx_rate_mbps{{mac="{mac_sanitized}",ssid="{ssid}",band="{band}"}}={rx_rate}')
    return output