import requests
import json

#zabbix  api
zabbix_url = "https://zabbix-server.net/api_jsonrpc.php"
zabbix_user = ""
zabbix_password = ""

#vender https://github.com/ytti/oxidized/blob/master/docs/Supported-OS-Types.md
vender_backup = "routeros"
#Credentinal for backup users 
user_backup = ""
pass_backup = ""
#enable = "password" #включение enable если используем, то добавляем file.write в самый конец {enable}

#Номер группы 
#how to search id group
#https://zabbix-server.net/zabbix.php?action=host.list&filter_set=1&filter_groups%5B0%5D=57
#last 57 this is id group
selected_group_id = "57" #указать номер группы в zabbix

auth_payload = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": zabbix_user,
        "password": zabbix_password
    },
    "id": 1,
    "auth": None
}

response = requests.post(zabbix_url, json=auth_payload)
auth_result = response.json()

if "result" in auth_result:
    auth_token = auth_result["result"]
else:
    print("Ошибка аутентификации:", auth_result.get("error", {}).get("data", "Нет данных"))
    exit()

# Получение узлов выбранной группы
host_payload = {
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output": ["hostid", "host"],
        "groupids": selected_group_id
    },
    "auth": auth_token,
    "id": 3
}

response = requests.post(zabbix_url, json=host_payload)
host_result = response.json()

if "result" in host_result:
    hosts = host_result["result"]

    # Проверяем существующие записи в router.db
    filename = "router.db"
    existing_entries = set()
    try:
        with open(filename, "r") as file:
            for line in file:
                existing_entries.add(line.strip())
    except FileNotFoundError:
        pass  # Ingnore file, not create file router.db

    # open file and add new string
    with open(filename, "a") as file:
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
                "id": 5
            }

            response = requests.post(zabbix_url, json=interface_payload)
            interface_result = response.json()

            if "result" in interface_result:
                interfaces = interface_result["result"]
                if interfaces:
                    ip_address = interfaces[0]["ip"]
                    entry = f"{host_name}:{vender_backup}:{ip_address}:{user_backup}:{pass_backup}"
                    if entry not in existing_entries:
                        file.write(f"{entry}\n")
                else:
                    error_message = f"Ошибка {host_id}, {host_name}, IP: Не найден"
                    if error_message not in existing_entries:
                        file.write(f"{error_message}\n")
            else:
                error_message = f"Ошибка при получении IP-адреса для узла {host_name}"
                if error_message not in existing_entries:
                    file.write(f"{error_message}\n")
else:
    print("Ошибка при получении узлов:", host_result.get("error", {}).get("data", "Нет данных"))
    exit()

# Завершение сессии
logout_payload = {
    "jsonrpc": "2.0",
    "method": "user.logout",
    "params": [],
    "id": 4,
    "auth": auth_token
}

requests.post(zabbix_url, json=logout_payload)
