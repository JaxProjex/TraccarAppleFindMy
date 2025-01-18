import json
import os
import time
import requests
from urllib.parse import urlencode
import signal
import subprocess
import sys

# sudo pmset disablesleep 1 //run this in console to prevent mac from sleeping
# sudo pmset disablesleep 0 //run this in console to TURN OFF prevent mac from sleeping


TRACCAR_SERVER = "http://10.237.104.84" #set ip address of traccar server, dont add port 5055
COMPUTER_USER = 'oldmac' #set user for proper filepath


DEVICES_FILE = f'/Users/{COMPUTER_USER}/Library/Caches/com.apple.findmy.fmipcore/Devices.data'
ITEMS_FILE = f'/Users/{COMPUTER_USER}/Library/Caches/com.apple.findmy.fmipcore/Items.data'

def read_data(file):
    with open(file, 'r') as f:
        return json.load(f)

items_data = read_data(ITEMS_FILE)
devices_data = read_data(DEVICES_FILE)

items_ref = {}
devices_ref = {}

def postTraccar(body):
    print("post traccar")
    id = body["id"]
    try:
        response = requests.post(f"{TRACCAR_SERVER}:5055", params=body)
        if response.status_code == 200:
            print(f"sent {id} successfully")
        else:
            print(f"{id} failed to send")
    except requests.RequestException as e:
        print(f"error sending data: {e}")


def updateItems(): #airtags
    global items_ref
    for item in read_data(ITEMS_FILE):
        if item.get("location") is None:
            continue

        lat = item["location"]["latitude"]
        lon = item["location"]["longitude"]
        timestamp = item["location"]["timeStamp"]

        lat1 = lat
        lon1 = lon
        timestamp1 = timestamp
        
        if item.get("crowdSourcedLocation"):
            lat1 = item["crowdSourcedLocation"]["latitude"]
            lon1 = item["crowdSourcedLocation"]["longitude"]
            timestamp1 = item["crowdSourcedLocation"]["timeStamp"]

        name = item["name"]
        sn = item["serialNumber"]

        if sn not in items_ref:
            print(f"adding new item {sn}")
            items_ref[sn] = [timestamp, timestamp1]

        old_timestamp = items_ref[sn][0]
        old_timestamp1 = items_ref[sn][1]
        print(f"{name} at {lat},{lon} time:{timestamp} compared to {old_timestamp} and time1:{timestamp1} to {old_timestamp1}")

        if timestamp != items_ref[sn][0] or timestamp1 != items_ref[sn][1]:
            if timestamp != items_ref[sn][0]:
                items_ref[sn][0] = timestamp
                params = {"id": name, "lat": lat, "lon": lon}
                postTraccar(params)
            elif timestamp1 != items_ref[sn][1]:
                items_ref[sn][1] = timestamp1 
                params = {"id": name, "lat": lat1, "lon": lon1}
                postTraccar(params)  

def updateDevices(): #phones,tablets,computers,watches
    global devices_ref
    for device in read_data(DEVICES_FILE):
        if device.get("location") is None:
            continue

        lat = device["location"]["latitude"] 
        lon = device["location"]["longitude"]
        timestamp = device["location"]["timeStamp"]

        lat1 = lat
        lon1 = lon
        timestamp1 = timestamp

        if device.get("crowdSourcedLocation"):
            lat1 = device["crowdSourcedLocation"]["latitude"]
            lon1 = device["crowdSourcedLocation"]["longitude"]
            timestamp1 = device["crowdSourcedLocation"]["timeStamp"]

        name = device["name"]
        sn = device["id"]
        
        if sn not in devices_ref:
            print(f"adding new device {sn}")
            devices_ref[sn] = [timestamp, timestamp1]

        old_timestamp = devices_ref[sn][0]
        old_timestamp1 = devices_ref[sn][1]
        print(f"{name} at {lat},{lon} time:{timestamp} compared to {old_timestamp} and time1:{timestamp1} to {old_timestamp1}")
        
        if timestamp != devices_ref[sn][0] or timestamp1 != devices_ref[sn][1]:
            if timestamp != devices_ref[sn][0]:
                devices_ref[sn][0] = timestamp
                params = {"id": name, "lat": lat, "lon": lon}
                postTraccar(params)
            elif timestamp1 != devices_ref[sn][1]:
                devices_ref[sn][1] = timestamp
                params = {"id": name, "lat": lat1, "lon": lon1}
                postTraccar(params)

def turnSleepOn(signal, frame): #when Ctr^C pressed allow mac to sleep
    print("turnSleepOn")
    subprocess.run(["sudo", "pmset", "disablesleep", "0"])
    sys.exit(0)

signal.signal(signal.SIGINT, turnSleepOn)

def main():
    subprocess.run(["sudo", "pmset", "disablesleep", "1"]) #dont let mac sleep to allow script to run forever.. and ever.
    while True:
        print("while loop iteration")
        updateItems()
        time.sleep(1)
        updateDevices()
        time.sleep(59)

main()

print("exiting traccarFindMy")
