# collector/parsers.py
import re

def _format_labels(labels_dict):
    """Helper to convert a dictionary of labels to a Prometheus label string."""
    if not labels_dict: return ""
    return "{" + ",".join([f'{k}="{v}"' for k, v in sorted(labels_dict.items())]) + "}"

def parse_key_value(lines, command_prefix, base_labels, separator=':'):
    output = []
    labels_str = _format_labels(base_labels)
    for line in lines:
        if separator not in line: continue
        parts = line.split(separator, 1)
        if len(parts) != 2: continue
        key, value = parts[0].strip(), parts[1].strip()
        try:
            float(value)
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).lower()
            output.append(f"{command_prefix}_{clean_key}{labels_str}={value}")
        except ValueError:
            continue
    return output

def parse_deviceinfo(lines, command_prefix, base_labels):
    output = []
    labels_str = _format_labels(base_labels)
    for line in lines:
        if '=' not in line: continue
        key, value_str = [p.strip() for p in line.split('=', 1)]
        key = key.lower()
        if key == 'uptime':
            match = re.search(r'(\d+)\s*day\(s\)\s*(\d{2}):(\d{2}):(\d{2})', value_str)
            if match:
                days, h, m, s = map(int, match.groups())
                total_seconds = (days * 86400) + (h * 3600) + (m * 60) + s
                output.append(f"{command_prefix}_uptime_seconds{labels_str}={total_seconds}")
        elif key == 'totalmemory':
            match = re.search(r'(\d+)', value_str)
            if match: output.append(f"{command_prefix}_total_memory_mb{labels_str}={match.group(1)}")
        elif key == 'totalflash':
            match = re.search(r'(\d+)', value_str)
            if match: output.append(f"{command_prefix}_total_flash_mb{labels_str}={match.group(1)}")
    return output

def parse_dhcp_server(lines, command_prefix, base_labels):
    output, total_users = [], 0
    for line in lines:
        if line.strip().startswith('Total:'):
            total_users = line.strip().split(':')[1].strip()
            continue
        match = re.match(r'^\s*(\d+)\s+(\S+)\s+([0-9.]+)\s+(\S+)\s+([0-9a-f:]+)\s+(.*)$', line, re.I)
        if match:
            index, port, ip, hostname, mac, expire_str = match.groups()
            specific_labels = {'index': index, 'port': port, 'ip': ip, 'hostname': hostname.strip(), 'mac': mac}
            all_labels = {**base_labels, **specific_labels}
            labels_str = _format_labels(all_labels)
            output.append(f'{command_prefix}_lease_info{labels_str} 1')
            expire_match = re.search(r'(\d+)\s*days,\s*(\d{2}):(\d{2}):(\d{2})', expire_str)
            if expire_match:
                days, h, m, s = map(int, expire_match.groups())
                total_seconds = (days * 86400) + (h * 3600) + (m * 60) + s
                output.append(f'{command_prefix}_lease_expire_seconds{labels_str}={total_seconds}')
    if total_users:
        output.append(f'{command_prefix}_total_users{_format_labels(base_labels)}={total_users}')
    return output

def parse_waninfo_all_detail(lines, command_prefix, base_labels):
    output, current_wan_info = [], {}
    def process_block(info):
        if not info or "interface" not in info: return
        ip_address = info.get("ipv4_address", "").split('/')[0]
        specific_labels = {'interface': info.get("interface"), 'hw_addr': info.get("hw_addr",""), 'ip_address': ip_address}
        all_labels = {**base_labels, **specific_labels}
        labels_str = _format_labels(all_labels)
        status_numeric = 1 if info.get("status", "").lower() == 'enable' else 0
        output.append(f'{command_prefix}_status{labels_str}={status_numeric}')
        if info.get("vlan", "").isdigit(): output.append(f'{command_prefix}_vlan{labels_str}={info.get("vlan")}')
        if info.get("mtu", "").isdigit(): output.append(f'{command_prefix}_mtu{labels_str}={info.get("mtu")}')
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

def parse_lanport_workmode(lines, command_prefix, base_labels):
    output = []
    for line in lines:
        match = re.match(r'^\s*(\d+)\s+([\w\d]+)\s+([\w\s]+)\s*$', line)
        if match:
            index, name, mode_str = match.groups()
            specific_labels = {'index': index, 'name': name, 'workmode': mode_str.strip()}
            all_labels = {**base_labels, **specific_labels}
            labels_str = _format_labels(all_labels)
            output.append(f'{command_prefix}_info{labels_str} 1')
    return output

def parse_wifi_associate(lines, command_prefix, base_labels):
    output, band = [], None
    for line in lines:
        if "2.4GHz" in line: band = "2.4GHz"
        elif "5GHz" in line: band = "5GHz"
        match = re.match(r'^([0-9A-F:]{17})\s+(\S+)\s+(\d+)\s+(\d+)M\s+(\d+)M.*$', line, re.I)
        if match and band:
            mac, ssid, time_sec, tx_rate, rx_rate = match.groups()
            specific_labels = {'mac': mac.replace(':', ''), 'ssid': ssid, 'band': band}
            all_labels = {**base_labels, **specific_labels}
            labels_str = _format_labels(all_labels)
            output.append(f'{command_prefix}_uptime_seconds{labels_str}={time_sec}')
            output.append(f'{command_prefix}_tx_rate_mbps{labels_str}={tx_rate}')
            output.append(f'{command_prefix}_rx_rate_mbps{labels_str}={rx_rate}')
    return output

def parse_wifi_information(lines, command_prefix, base_labels):
    output, current_ssid_info = [], {}
    def process_block(info):
        if not info or "ssid_index" not in info: return
        specific_labels = {'ssid_index': info.get("ssid_index"), 'ssid_name': info.get("ssid","")}
        all_labels = {**base_labels, **specific_labels}
        labels_str = _format_labels(all_labels)
        status_numeric = 1 if info.get("status", "").lower() == 'up' else 0
        output.append(f'{command_prefix}_status{labels_str}={status_numeric}')
        channel_match = re.search(r'(\d+)', info.get("channel", ""))
        if channel_match: output.append(f'{command_prefix}_channel{labels_str}={channel_match.group(1)}')
        rate_match = re.search(r'(\d+)\s*M', info.get("supported_max_rate", ""))
        if rate_match: output.append(f'{command_prefix}_max_rate_mbps{labels_str}={rate_match.group(1)}')
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

def parse_wap_top(lines, command_prefix, base_labels):
    output = []
    labels_str = _format_labels(base_labels)
    for line in lines:
        if line.strip().startswith('Mem:'):
            parts = re.findall(r'(\d+)K\s+(\w+)', line)
            for value, key in parts: output.append(f"{command_prefix}_mem_{key}_kb{labels_str}={value}")
        elif line.strip().startswith('CPU:'):
            parts = re.findall(r'(\d+\.\d+)%\s+(\w+)', line)
            for value, key in parts: output.append(f"{command_prefix}_cpu_{key}_percent{labels_str}={value}")
        elif line.strip().startswith('Load average:'):
            match = re.search(r'Load average:\s+([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)', line)
            if not match: match = re.search(r'Load average:\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
            if match:
                load_1m, load_5m, load_15m = match.groups()
                output.append(f"{command_prefix}_load_average_1m{labels_str}={load_1m}")
                output.append(f"{command_prefix}_load_average_5m{labels_str}={load_5m}")
                output.append(f"{command_prefix}_load_average_15m{labels_str}={load_15m}")
    return output

def parse_sfwd_drop(lines, command_prefix, base_labels):
    output = []
    labels_str = _format_labels(base_labels)
    for line in lines:
        if ':' in line and not line.strip().startswith('['):
            key, value = [p.strip() for p in line.split(':', 1)]
            output.append(f"{command_prefix}_{key}{labels_str}={value}")
    header_line, value_line = None, None
    for i, line in enumerate(lines):
        if 'bcast' in line and 'arp' in line:
            header_line = line.strip().split()
            if i + 1 < len(lines): value_line = lines[i+1].strip().split()
            break
    if header_line and value_line:
        for key, value in zip(header_line, value_line):
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).lower()
            output.append(f"{command_prefix}_protocol_{clean_key}{labels_str}={value}")
    return output
