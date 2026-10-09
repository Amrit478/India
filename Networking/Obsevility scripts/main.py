#!/usr/bin/env python3

import os
import sys
import yaml

from jinja2 import Environment, FileSystemLoader


VARS_FILE = "vars.yaml"
TEMPLATE_FILE = "cisco_logging.j2"
OUTPUT_DIR = "output"


def load_data(filename):
    """Load YAML configuration data."""

    try:
        with open(filename, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            print(f"[!] Error: {filename} is empty.", file=sys.stderr)
            sys.exit(1)

        return data

    except FileNotFoundError:
        print(f"[!] Error: {filename} not found.", file=sys.stderr)
        sys.exit(1)

    except yaml.YAMLError as e:
        print(f"[!] YAML error: {e}", file=sys.stderr)
        sys.exit(1)


def render_config(env, template_name, global_vars, device):
    """Render the Jinja configuration for one device."""

    template = env.get_template(template_name)

    return template.render(
        collector_ip=global_vars.get("collector_ip"),
        ntp_server=global_vars.get("ntp_server"),
        snmp_community=global_vars.get("snmp_community", "public"),
        netflow_export_port=global_vars.get("netflow_export_port", 2055),
        syslog_port=global_vars.get("syslog_port", 1514),
        netflow_protocol=global_vars.get("netflow_protocol", "ipfix"),
        device=device
    )


def main():

    print("[*] Loading configuration...")

    data = load_data(VARS_FILE)

    devices = data.get("devices", [])

    if not devices:
        print("[!] No devices found in vars.yaml.", file=sys.stderr)
        sys.exit(1)

    # Create Jinja environment
    env = Environment(
        loader=FileSystemLoader("."),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[*] Found {len(devices)} devices.")

    # Render configuration for every device
    for device in devices:

        hostname = device.get("hostname", "Unknown")

        print(f"[*] Rendering configuration for {hostname}...")

        config = render_config(
            env,
            TEMPLATE_FILE,
            data,
            device
        )

        output_file = os.path.join(
            OUTPUT_DIR,
            f"{hostname}.cfg"
        )

        with open(output_file, "w") as f:
            f.write(config)

        print(f"[+] Created: {output_file}")

    print()
    print("[+] Configuration generation completed.")
    print(f"[*] Files are located in: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
