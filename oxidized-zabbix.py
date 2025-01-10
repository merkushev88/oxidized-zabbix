import requests
import json
import os

zabbix_url = "http://zabbix_server/api_jsonrpc.php"
zabbix_user = "user_zabbix"
zabbix_password = "password"

# Senttings Zabbix group and device oxidized
groups_config = {
    "routeros": {
        "filename": "/some/path/to/filedb/router.db",
        "vendor": "routeros",
        "user": "backup_user",
        "password": "backup_password_device",
        "zabbix_group_id": "1"  # ID group in Zabbix
    },
    "asa-cisco": {
        "filename": "/home/adminlinux/.config/oxidized/router.db",
        "vendor": "asa",
        "user": "backup_user",
        "password": "password_backup",
        "enable_password": "enable_passeword",
        "enable_level": "3", 
       "zabbix_group_id": "2"  # ID group in Zabbix
    }

}

auth_payload = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": zabbix_user,
        "password": zabbix_password
    },
    "id": 1
}

response = requests.post(zabbix_url, json=auth_payload)
auth_result = response.json()

if "result" in auth_result:
    auth_token = auth_result["result"]
else:
    print("ERROR AUTH:", auth_result.get("error", {}).get("data", "Some error"))
    exit()

for group in groups_config.values():
    with open(group["filename"], "w") as file:
        pass

for group_name, group in groups_config.items():
    print(f"Обрабатывается группа: {group_name}")
    
    host_payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host"],
            "groupids": group["zabbix_group_id"],
            "filter": {
                "status": "0"  # ONLY active device
            }
        },
        "auth": auth_token,
        "id": 2
    }

    response = requests.post(zabbix_url, json=host_payload)
    host_result = response.json()

    if "result" in host_result:
        hosts = host_result["result"]

        
        for host in hosts:
            host_id = host['hostid']
            host_name = host['host']

            
            interface_payload = {
                "jsonrpc": "2.0",
                "method": "hostinterface.get",
                "params": {
                    "output": ["ip"],
                    "hostids": host_id
                },
                "auth": auth_token,
                "id": 3
            }

            response = requests.post(zabbix_url, json=interface_payload)
            interface_result = response.json()

            if "result" in interface_result:
                interfaces = interface_result["result"]
                if interfaces:
                    ip_address = interfaces[0]["ip"]

                    # String for save router.db
                    line = f"{host_name}:{group['vendor']}:{ip_address}:{group['user']}:{group['password']}"

                    # If you need something settings,  enable, level etc
                    if group.get("enable_password"):
                        line += f":{group['enable_password']}"

                    if group.get("enable_level"):
                        line += f":{group['enable_level']}"

                    # Save routerdb
                    with open(group["filename"], "a") as file:
                        file.write(line + "\n")

                else:
                    print(f"Device {host_name} did'nt have IP.")
            else:
                print(f"Error read device {host_name}.")
    else:
        print(f"Eror {group_name}: {host_result.get('error', {}).get('data', 'Unknow error')}")
logout_payload = {
    "jsonrpc": "2.0",
    "method": "user.logout",
    "params": [],
    "id": 4,
    "auth": auth_token
}

requests.post(zabbix_url, json=logout_payload)
print("Finish.")
