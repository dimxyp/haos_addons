

# 🔍 DNS IP Monitor Add-on for Home Assistant

This add-on created due to many issues that I have using https://www.home-assistant.io/integrations/dnsip/ (many unreachable changes many wrong states etc)

This custom Home Assistant add-on monitors the IPv4 address of up to 5 domain names using DNS lookups (`nslookup`). If the IP address of any domain changes, it updates the corresponding `input_text` entity in Home Assistant via its API.

---

## 📦 Features

- Monitors up to 5 DNS hostnames (`URL1` to `URL5`)
- Performs DNS lookup every 5 minutes
- Detects IPv4 changes
- Updates `input_text.url1` to `input_text.url5` using Home Assistant's REST API
- Skips unset or invalid URLs
- Prints clear logs and changes to the add-on log panel
- ASCII banner and startup message 🎉

---

## 🛠️ Configuration

Edit the add-on configuration in Home Assistant UI:

```yaml
haip: ha private ip
token: ACCESS_TOKEN
URL1: www.google.com
URL2: example.com
URL3: NULL
URL4: NULL
URL5: NULL
```

🧪 Example
If www.google.com resolves to 142.250.185.68, it updates:

```
input_text.url1 → 142.250.185.68
```
If the IP changes on the next check, it updates again. If unchanged, nothing happens.



✅ Requirements
 
> input_text.url1 through input_text.url5 must be created in your config or via Helpers
> 
> Long-lived token from a Home Assistant user
