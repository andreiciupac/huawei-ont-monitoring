# collector/parsers.py
import re

def parse_key_value(lines, command_prefix, separator=':'):
    """Parses simple key: value or key = value formats, only for numeric values."""
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

def parse_deviceinfo(lines, command_prefix):
    """Dedicated parser for 'display deviceinfo' to handle specific fields."""
    output = []
    for line in lines:
        if '=' not in line: continue
        key, value_str = [p.strip() for p in line.split('=', 1)]
        value_str = value_str.strip()
        key = key.lower()

        if key == 'uptime':
            days, hours, minutes, seconds = 0, 0, 0, 0
            match = re.search(r'(\d+)\s*day\(s\)\s*(\d{2}):(\d{2}):(\d{2})', value_str)
            if match:
                days, hours, minutes, seconds = map(int, match.groups())
            total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
            output.append(f"{command_prefix}_uptime_seconds={total_seconds}")
        elif key == 'totalmemory':
            match = re.search(r'(\d+)\s*Mbytes', value_str)
            if match:
                output.append(f"{command_prefix}_total_memory_mb={match.group(1)}")
        elif key == 'totalflash':
            match = re.search(r'(\d+)\s*Mbytes', value_str)
            if match:
                output.append(f"{command_prefix}_total_flash_mb={match.group(1)}")
    return output

def parse_dhcp_server(lines, command_prefix):
    """Parses the 'display dhcp server user all' table with expire time."""
    output = []
    total_users = 0
    for line in lines:
        if line.strip().startswith('Total:'):
            total_users = line.strip().split(':')[1].strip()
            continue
        match = re.match(r'^\s*(\d+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\s+([0-9a-f:]+)\s+(.*)$', line, re.I)
        if match:
            index, port, ip, hostname, mac, expire_time = match.groups()
            output.append(f'{command_prefix}_lease_info{{index="{index}",port="{port}",ip="{ip}",hostname="{hostname.strip()}",mac="{mac}",expire_time="{expire_time.strip()}"}} 1')
    if total_users:
        output.append(f'{command_prefix}_total_users={total_users}')
    return output

def parse_wifi_information(lines, command_prefix):
    """Parses multi-block 'display wifi information' using labels."""
    output = []
    current_ssid_info = {}
    def process_block(info):
        if not info or "ssid_index" not in info: return
        labels = f'ssid_index="{info.get("ssid_index")}",ssid_name="{info.get("ssid","")}"'
        status_numeric = 1 if info.get("status", "").lower() == 'up' else 0
        output.append(f'{command_prefix}_status{{{labels}}}={status_numeric}')
        channel_match = re.search(r'(\d+)', info.get("channel", ""))
        if channel_match: output.append(f'{command_prefix}_channel{{{labels}}}={channel_match.group(1)}')
        rate_match = re.search(r'(\d+)\s*M', info.get("supported_max_rate", ""))
        if rate_match: output.append(f'{command_prefix}_max_rate_mbps{{{labels}}}={rate_match.group(1)}')
    for line in lines:
        if "---" in line:
            process_block(current_ssid_info)
            current_ssid_info = {}
            continue
        if ':' in line:
            key, value = [p.strip() for p in line.split(':', 1)]
            current_ssid_info[key.lower().replace(' ', '_')] = value
    process_block(current_ssid_info)
    return output

def parse_waninfo_all_detail(lines, command_prefix):
    """Dedicated parser for 'display waninfo all detail'."""
    output = []
    current_wan_info = {}
    def process_block(info):
        if not info or "interface" not in info: return
        labels = f'interface="{info.get("interface")}",hw_addr="{info.get("hw_addr","")}"'
        status_numeric = 1 if info.get("status", "").lower() == 'enable' else 0
        output.append(f'{command_prefix}_status{{{labels}}}={status_numeric}')
        if info.get("vlan", "").isdigit(): output.append(f'{command_prefix}_vlan{{{labels}}}={info.get("vlan")}')
        if info.get("mtu", "").isdigit(): output.append(f'{command_prefix}_mtu{{{labels}}}={info.get("mtu")}')
    for line in lines:
        if "---" in line:
            process_block(current_wan_info)
            current_wan_info = {}
            continue
        if ':' in line:
            key, value = [p.strip() for p in line.split(':', 1)]
            current_wan_info[key.lower().replace(' ', '_').replace('.', '')] = value
    process_block(current_wan_info)
    return output

def parse_cpu_info(lines, command_prefix):
    """Parses the multi-record format of 'display cpu info'."""
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
    """Parses 'wap top' to get memory, CPU, and load average usage."""
    output = []
    for line in lines:
        if line.strip().startswith('Mem:'):
            parts = re.findall(r'(\d+)K\s+(\w+)', line)
            for value, key in parts: output.append(f"{command_prefix}_mem_{key}_kb={value}")
        elif line.strip().startswith('CPU:'):
            parts = re.findall(r'(\d+\.\d+)%\s+(\w+)', line)
            for value, key in parts: output.append(f"{command_prefix}_cpu_{key}_percent={value}")
        elif line.strip().startswith('Load average:'):
            match = re.search(r'Load average:\s+([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)', line)
            if not match: match = re.search(r'Load average:\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
            if match:
                load_1m, load_5m, load_15m = match.groups()
                output.append(f"{command_prefix}_load_average_1m={load_1m}")
                output.append(f"{command_prefix}_load_average_5m={load_5m}")
                output.append(f"{command_prefix}_load_average_15m={load_15m}")
    return output

def parse_sfwd_drop(lines, command_prefix):
    """Parses the two-part table in 'sfwd drop statistics'."""
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
    """Parses the 'display lanport workmode' table using the labels-as-columns pattern."""
    output = []
    for line in lines:
        match = re.match(r'^\s*(\d+)\s+([\w\d]+)\s+([\w\s]+)\s*$', line)
        if match:
            index, name, mode_str = match.groups()
            output.append(f'{command_prefix}_info{{index="{index}",name="{name}",workmode="{mode_str.strip()}"}} 1')
    return output

def parse_wifi_associate(lines, command_prefix):
    """Parses 'display wifi associate' to get stats for each connected device."""
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