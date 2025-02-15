import time
import websocket
import threading
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from typing import cast
from dotenv import load_dotenv
import os

def on_service_state_change(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
    print(f"Service {name} of type {service_type} state changed: {state_change}")

    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        print(f"Info from zeroconf.get_service_info: {info!r}")

        if info:
            addresses = [f"{addr}:{cast(int, info.port)}" for addr in info.parsed_scoped_addresses()]
            print(f"  Addresses: {', '.join(addresses)}")
            print(f"  Weight: {info.weight}, priority: {info.priority}")
            print(f"  Server: {info.server}")
            if info.properties:
                print("  Properties are:")
                for key, value in info.properties.items():
                    print(f"    {key!r}: {value!r}")
            else:
                print("  No properties")
        else:
            print("  No info")
        print("\n")

def on_close(ws):
    print("Disconnected from server")
    print("Retry : %s" % time.ctime())

    time.sleep(10)
    connect_to_homeassistant() # retry per 10 seconds

    # If we fail three times to reconnect, initial the "safe-guard"
    #

def on_open(ws):
    print('connection established')

def on_message(ws, message):
    print(message)

def connect_to_homeassistant():

    print("Connecting to Home Assistant")

    # Fetch the Home Assistant websocket host and key from the environment.
    #
    homeassistant_host = os.getenv("HOME_ASSISTANT_WEBSOCKET_HOST")
    homeassistant_token = os.getenv("HOME_ASSISTANT_WEBSOCKET_TOKEN")

    print(homeassistant_host)
    print(homeassistant_token)

    url = "ws://{}".format(homeassistant_host)

    ws = websocket.WebSocketApp(url, on_open = on_open, on_close = on_close, on_message=on_message)

    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

def main():

    load_dotenv()

    # Using mDNS, find all Shelly devices on the network.
    #
    print(f'Scanning for Shelly devices for {30} seconds')

    # zeroconf = Zeroconf()

    # browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])

    # # We will give the script 30 seconds to find all Shelly devices.
    # #
    # time.sleep(30000)
    
    # zeroconf.close()

    # With a list of all Shelly Devices in memory, open a channel to Home Assistant.
    #
    try:
        connect_to_homeassistant()
    except Exception as err:
        print(err)
        print("Connection failed")

if __name__ == "__main__":
    main()
    
