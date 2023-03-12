# shellyplug.py

## About
CLI for [Shelly Plug / PlugS](https://shelly-api-docs.shelly.cloud/gen1/#shelly-plug-plugs).


## Screenshots
![shellyplugpy](https://user-images.githubusercontent.com/16217416/224556525-0d0f0c92-716f-41c1-a66a-766342ce0112.png)


## Settings
See line 20-25 in the script:
```
# --- settings
plugs = ["192.168.33.1", "shelly01.your.lan"] # IP or FQDN
currency = "€"
energy_price = 0.379 # currency per kWh
volt = 230 # amp calc
timeout = 3 # seconds
polling_interval = 1 # seconds
```