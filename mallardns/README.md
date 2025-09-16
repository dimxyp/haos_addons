# 🌐 Mallard DNS Add-on for Home Assistant

> Mallard ducks are remarkably **intelligent** birds, known for their ability to navigate complex social structures, communicate through vocalizations and body language, and even recognize and return to familiar locations


## 📦 Based on official Home Assistant Add-on: DuckDNS .. 🦆 🙏 but smarter...
> [!IMPORTANT]
> `This add-on would not have been possible without the work of the developers who created the official DuckDNS add-on`

All the options etc is based on https://github.com/home-assistant/addons/tree/master/duckdns this addon only adds 2 Firewall commands for isolated Home Assistance environments, open NAT/PAT Port before SSL renewall and close after that.


## 🧱 Firewall Part

- ### fwh  -  Firewall Host Command

Insert your firewall host configuration here. e.g. root@192.168.1.1 

The full command is based on below, so the authentication is based on ssh key id_rsa for your firewall connectivity.
```yaml
ssh -i /config/.ssh/id_rsa -o 'PubkeyAcceptedKeyTypes +ssh-rsa' -o StrictHostKeyChecking=no 
```


- ### fwco - Firewall Command Command Open Port 🔓

Insert your firewall command to open port here. e.g. /ip firewall nat enable XXXX

- ### fwcc - Firewall Command Command Close Port 🔒

Insert your firewall command to close port here. e.g. /ip firewall nat disable XXXX

## 🛡️ Mikrotik Example

- fwh: admin@172.17.1.1
- fwco: /ip firewall nat enable [find comment="Marllard"]
- fwcc: /ip firewall nat disable [find comment="Marllard"]

```yaml
#Mikrotik NAT config:
- 18 X  ;;; Marllard
      chain=dstnat action=dst-nat to-addresses=192.168.X.X to-ports=XXXX protocol=tcp in-interface-list=WAN dst-port=XXXX log=no" 
```

🛠️ Dependencies
- ssh-key authentication between Home Assistant and your Firewall
- Create NAT/PAT rule
- Commands for enable/disable above rule
- all the knwon DuckDNS add-on requirements

## About

[Duck DNS][duckdns] is a free service that points a DNS (sub-domains of duckdns.org) to an IP of your choice. This add-on includes support for Let’s Encrypt and automatically creates and renews your certificates. You need to sign up for a Duck DNS account before using this add-on.

