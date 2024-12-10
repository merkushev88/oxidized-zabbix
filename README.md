# oxidized-zabbix
script import device from zabbix API to oxidized

example config map device 
``` text
source:
  default: csv
  csv:
    file: ".config/oxidized/router.db"
    delimiter: !ruby/regexp /:/
    map:
      name: 0
      model: 1
      ip: 2
      username: 3
      password: 4"
