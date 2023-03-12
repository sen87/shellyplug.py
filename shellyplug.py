#!/usr/bin/python
# -*- coding: utf-8 -*-
# sen <s3n87@pm.me>
info = """
┌──────────────────────────────────────────────────
│ Shelly Plug Control
│ v0.2
├──────────────────────────────────────────────────
│ Parameter:
│ <IP/FQDN>             connect to specified plug
│ <none>                load plugs from list
│                       ("plugs" array in settings)
├──────────────────────
│ Non-Interactive Mode:
│ --toggle <IP/FQDN>    toggle relay state
│ --on <IP/FQDN>        turn relay on
│ --off <IP/FQDN>       turn relay off
└──────────────────────────────────────────────────\n"""
# --- settings
plugs = ["192.168.33.1", "shelly01.your.lan"] # IP or FQDN
currency = "€"
energy_price = 0.379 # currency per kWh
volt = 230 # amp calc
timeout = 3 # seconds
polling_interval = 1 # seconds
# --- imports
import asyncio
import json
from os import _exit, system
from select import select
from sys import argv, stdin
import termios
import tty
import urllib.request
# --- text
reset = "\033[0m"
bold_on = "\033[1m"
bold_off = "\033[22m"
col_black = "\033[30m"
col_blue = "\033[34m"
col_cyan = "\033[36m"
col_green = "\033[32m"
col_purple = "\033[35m"
col_red = "\033[31m"
col_white = "\033[37m"
col_yellow = "\033[33m"
# --- init values
shelly = ""
shelly_ip = ""
shelly_ssid = ""
shelly_relay = False
shelly_timer = False
shelly_timer_dur = 0
shelly_timer_rem = 0
shelly_power = 0.0
shelly_opp = 0.0
shelly_kwh = 0.0
shelly_time = ""
shelly_uptime = 0
shelly_fw = ""

async def shelly_update():
    global shelly_ip, shelly_ssid, shelly_relay, shelly_timer, shelly_timer_dur, shelly_timer_rem, shelly_power, \
           shelly_opp, shelly_kwh, shelly_time, shelly_uptime, shelly_fw
    while True:
        try:
            req = urllib.request.Request(f"http://{shelly}/status")
            response = urllib.request.urlopen(req, timeout=timeout)
            data = response.read()
            shelly_val = json.loads(data)
            # - wifi
            shelly_ip = shelly_val["wifi_sta"]["ip"]
            shelly_ssid = shelly_val["wifi_sta"]["ssid"]
            # - relay
            shelly_relay = shelly_val["relays"][0]["ison"]
            shelly_timer = shelly_val["relays"][0]["has_timer"]
            shelly_timer_dur = shelly_val["relays"][0]["timer_duration"]
            shelly_timer_rem = shelly_val["relays"][0]["timer_remaining"]
            # - relay
            shelly_power = shelly_val["meters"][0]["power"]
            shelly_opp = shelly_val["meters"][0]["overpower"]
            shelly_kwh = round((shelly_val["meters"][0]["total"] / 1000 ) / 60, 2)
            # - sys
            shelly_time = shelly_val["time"]
            shelly_uptime = shelly_val["uptime"]
            shelly_fw = shelly_val["update"]["old_version"]
        except urllib.error.URLError:
            shelly_ip = ""
            shelly_ssid = ""
            shelly_relay = False
            shelly_timer = False
            shelly_timer_dur = 0
            shelly_timer_rem = 0
            shelly_power = 0.0
            shelly_opp = 0.0
            shelly_kwh = 0.0
            shelly_time = ""
            shelly_uptime = 0
            shelly_fw = ""
        await asyncio.sleep(polling_interval)

def shelly_control(action): # actions = on, off, toggle
    try:
        urllib.request.urlopen(f"http://{shelly}/relay/0?turn={action}", data=None, timeout=timeout)
    except urllib.error.URLError:
        print("[ERROR] could not connect to: " + shelly)

async def shelly_status():
    while True:
        # - checks
        if shelly_relay:
            col_state = col_green
            state1= "⠀⠀⠀⣀⣀⣀⣀⠀⣀⣀⣀⣀⠀⠀⠀⠀"
            state2= "⠀⠀⢸⠀⠀⠀⠀⡇⠀⠀⡇⠀⡇⠀⠀⠀"
            state3= "⠀⠀⢸⠀⠀⡇⠀⡇⠀⡇⡇⠀⡇⠀⠀⠀"
            state4= "⠀⠀⢸⣀⣀⣀⣀⡇⣀⡇⣀⣀⡇⠀⠀⠀"
        else:
            col_state = col_red
            state1= "⠀⣀⣀⣀⣀⠀⣀⣀⣀⣀⠀⣀⣀⣀⣀⠀"
            state2= "⢸⠀⠀⠀⠀⡇⠀⠀⣀⣀⡇⠀⠀⣀⣀⡇"
            state3= "⢸⠀⠀⡇⠀⡇⠀⠀⣀⣀⡇⠀⠀⣀⣀⡇"
            state4= "⢸⣀⣀⣀⣀⡇⣀⢸⠀⠀⡇⣀⢸⠀⠀⠀"
        if shelly_ssid:
            wifi = col_green + shelly_ssid
        else:
            wifi = col_red + "unreachable"
        if shelly_timer:
            timer = f"{convert_seconds(shelly_timer_rem)}{reset} [{convert_seconds(shelly_timer_dur)}]"
        else:
            timer = "disabled"
        if shelly_opp:
            power = f"{col_red}!!! OPP tripped: {shelly_opp}W !!!"
        else:
            if not shelly_power:
                power = col_white
            elif shelly_power >= 100:
                power = col_cyan
            elif shelly_power >= 1000:
                power = col_yellow
            elif shelly_power >= 3000:
                power = col_red
            else:
                power = col_green
            power += f"{shelly_power}W {reset}({(round(shelly_power / volt, 2))}A)"
        energy_costs = round(shelly_kwh * energy_price, 2)
        # - generate output
        out = f"{bold_on}{col_purple}p{col_white} Prev{bold_off}{col_state}⠀⠀⠀⠀⠀⠀⢀⣀⣀⡀⠀⠀⠀⠀⠀⠀" \
              f"{bold_on}{col_purple}n{col_white} Next⠀{bold_off}{col_black}┌─────────────────────────────────────────────" \
              f"{bold_on}{col_purple}\no{col_white} On{bold_off}{col_state}⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀" \
              f"{bold_on}{col_purple}s{col_white} Off⠀{bold_off}{col_black}│ {bold_on}{col_yellow}{shelly}{bold_off}" \
              f"{col_state}\n⠀⠀⠀⠀⠀⠀⠀⣀⣤⣶⡆⠀⢸⣿⣿⡇⠀⢰⣶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀{col_black}├─────────────────────────────────────────────" \
              f"{col_state}\n⠀⠀⠀⠀⠀⣤⣾⣿⣿⡿⠇⠀⢸⣿⣿⡇⠀⠸⢿⣿⣿⣷⣤⠀⠀⠀⠀⠀⠀{col_black}│ {col_blue}Wi-Fi   :  {wifi}" \
              f"{col_state}\n⠀⠀⠀⣠⣾⣿⣿⠟⠁⠀⠀⠀⢸⣿⣿⡇⠀⠀⠀⠈⠻⣿⣿⣷⣄⠀⠀⠀⠀{col_black}│ {col_blue}IP      :  {reset}{shelly_ip}" \
              f"{col_state}\n⠀⠀⢠⣿⣿⡟⠁⠀⠀⠀⠀⠀⢸⣿⣿⡇⠀⠀⠀⠀⠀⠈⢻⣿⣿⡄⠀⠀⠀{col_black}├─────────────────────────────────────────────" \
              f"{col_state}\n⠀⠀⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠸⠿⠿⠇⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⠀⠀⠀{col_black}│ {col_blue}Timer   :  {col_cyan}{timer}" \
              f"{col_state}\n⠀⢸⣿⣿⠁⠀{state1}⠀⠈⣿⣿⡇⠀⠀{col_black}├─────────────────────────────────────────────" \
              f"{col_state}\n⠀⢸⣿⣿⠀⠀{state2}⠀⠀⣿⣿⡇⠀⠀{col_black}│ {col_blue}Power   :  {power}" \
              f"{col_state}\n⠀⠘⣿⣿⣇⠀{state3}⠀⣸⣿⣿⠃⠀⠀{col_black}│ {col_blue}Total   :  {reset}{shelly_kwh}kWh ({col_yellow}{energy_costs}{currency}{reset})" \
              f"{col_state}\n⠀⠀⢹⣿⣿⣄{state4}⣠⣿⣿⡏⠀⠀⠀{col_black}├─────────────────────────────────────────────" \
              f"{col_state}\n⠀⠀⠀⢻⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⡟⠀⠀⠀⠀{col_black}│ {col_blue}Time    :  {reset}{shelly_time}" \
              f"{col_state}\n⠀⠀⠀⠀⠙⢿⣿⣿⣶⣤⣀⠀⠀⠀⠀⠀⠀⣀⣤⣶⣿⣿⡿⠋⠀⠀⠀⠀⠀{col_black}│ {col_blue}Uptime  :  {col_purple}{convert_seconds(shelly_uptime)}" \
              f"{col_state}\n⠀⠀⠀⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣶⣶⣿⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀{col_black}│ {col_blue}Firmware:  {reset}{shelly_fw}" \
              f"{bold_on}{col_purple}\nt{col_white} Toggle{bold_off}{col_state}⠀⠀⠉⠉⠛⠛⠛⠛⠉⠉⠀⠀⠀⠀" \
              f"{bold_on}{col_purple}q{col_white} Quit⠀{bold_off}{col_black}└─────────────────────────────────────────────{reset}"
        system("clear")
        print(out)
        await asyncio.sleep(1)

def convert_seconds(s):
    # - conversion
    m = h = d = y = 0
    m, s = divmod(s, 60)
    if m:
        h, m = divmod(m, 60)
    if h:
        d, h = divmod(h, 24)
    if d:
        y, d = divmod(d, 365)
    # - generate output
    out = ""
    if y:
        out += f"{y}y:"
    if d:
        out += f"{d}d:"
    if h:
        out += f"{h}h:"
    if m:
        out += f"{m}m:"
    return out + f"{s}s"

async def kbd_input(loop):
    tty_settings = termios.tcgetattr(stdin) # backup
    try:
        tty.setcbreak(stdin.fileno())
        while True:
            if select([stdin], [], [], 0) == ([stdin], [], []): # data in stdin
                key = stdin.read(1)
                if key == "q" or key == "\x1b": # \x1b = ESC
                    for task in asyncio.tasks.all_tasks(loop):
                        task.cancel()
                    break # stops asyncio loop
                if key == "o":
                    shelly_control("on")
                if key == "s":
                    shelly_control("off")
                if key == "t":
                    shelly_control("toggle")
                if key == "p":
                    shelly_switch("prev")
                if key == "n":
                    shelly_switch("next")
            await asyncio.sleep(1)
    finally: # restore
        termios.tcsetattr(stdin, termios.TCSADRAIN, tty_settings)

def shelly_switch(action):
    global shelly
    index = plugs.index(shelly)
    if action == "prev":
        index -= 1
    else:
        index += 1
    # - rotate
    if index >= len(plugs):
        index = 0
    elif index < 0:
        index = (len(plugs) -1)
    shelly = plugs[index]

# --- parse cli parameters
try:
    if not argv[1:]:
        if plugs:
            shelly = plugs[0]
        else:
            print("no plugs in list... exiting")
            _exit(1)
    else:
        para = argv[1:]
        if para[0] in ("-h", "--help"):
            print(info)
            _exit(0)
        elif len(para) == 2: # non-interactive mode
            shelly = para[1]
            if para[0] == "--toggle":
                shelly_control("toggle")
            elif para[0] == "--on":
                shelly_control("on")
            elif para[0] == "--off":
                shelly_control("off")
            else:
                print(info)
            _exit(0)
        else:
            shelly = para[0]
            if shelly not in plugs:
                plugs.append(shelly)
    # - asyncio loop
    loop = asyncio.new_event_loop()
    loop.create_task(shelly_update())
    loop.create_task(shelly_status())
    loop.run_until_complete(kbd_input(loop))
except asyncio.CancelledError:
    pass
except KeyboardInterrupt:
    print("[keyboard interrupt received]")
    _exit(0)
except BaseException as e:
    print("[ERROR]", e)
    _exit(1)
