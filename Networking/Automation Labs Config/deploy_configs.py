import os
import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

# Set up paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_FILE = os.path.join(BASE_DIR, "inventory", "hosts.yaml")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Load inventory and variables
with open(INVENTORY_FILE, "r") as f:
    inventory = yaml.safe_load(f)

for host in inventory.get("hosts", []):
    print(f"\n[+] Processing {host['name']} ({host['host']})...")
    
    # 1. Render Jinja2 Template
    template_name = host.get("template", "router_base.j2")
    template = env.get_template(template_name)
    rendered_config = template.render(device=host)
    
    # 2. Save rendered output to Output/ directory
    output_filepath = os.path.join(OUTPUT_DIR, f"{host['name']}.cfg")
    with open(output_filepath, "w") as f:
        f.write(rendered_config)
    print(f"    Saved rendered config to Output/{host['name']}.cfg")
    
    # 3. Deploy configuration via Netmiko
    device_params = {
        "device_type": host.get("device_type", "cisco_ios"),
        "host": host["host"],
        "username": host["username"],
        "password": host["password"],
        "secret": host.get("secret", host["password"]),
    }
    
    try:
        print(f"    Connecting over SSH to {host['host']}...")
        connection = ConnectHandler(**device_params)
        connection.enable()
        
        # Split rendered template into lines for config commands
        config_commands = [line.strip() for line in rendered_config.splitlines() if line.strip() and not line.startswith("!")]
        
        output = connection.send_config_set(config_commands)
        connection.save_config()
        connection.disconnect()
        print(f"    Successfully deployed configuration to {host['name']}!")
    except Exception as e:
        print(f"    [!] Failed to deploy to {host['name']}: {e}")