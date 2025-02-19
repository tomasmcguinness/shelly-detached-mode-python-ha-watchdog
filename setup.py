from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from aiohttp import ClientSession
from typing import cast
from shelly import Shelly
import time
import logging
import asyncio
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('client')

failsave_active = False

discovered_devices = []

def on_service_state_change(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
    print(f"Service {name} of type {service_type} state changed: {state_change}")

    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)

        if name.startswith("shelly1"):
            print("Found a Shelly1")

            if info:
                addresses = [f"{addr}:{cast(int, info.port)}" for addr in info.parsed_scoped_addresses()]
                print(f"  Addresses: {', '.join(addresses)}")

                discovered_devices.append(Shelly(name, addresses[0]))

async def process() -> None:

    logger.info(f'Processing {discovered_devices.count} Shelly1 devices')

    with open('setup.json', 'w') as f:

        shellys = {"detached_shellys":[]}

        shellys_holder = shellys["detached_shellys"]

        async with ClientSession() as session:
            for device in discovered_devices:
                try:
                    async with session.get(f'http://{device.address}/settings') as resp:
                        logger.info(f'Connected to {device.name}: {resp.status}')
                        data = await resp.json()
                        relay = data["relays"][0]
                        ison = relay["ison"]
                        btn_type = relay["btn_type"]

                        if btn_type == 'detached':
                            logger.info(f'Shelly1 {device.name} is in detached mode')
                            shellys_holder.append(device.name)
                            
                except Exception as e:
                    logger.error(e)

        json.dump(shellys, f)
        f.close()

        logger.info('Setup is complete. setup.json contains a list of all Shelly1 relays in detached mode!')

if __name__ == '__main__':

    # Using mDNS, find all Shelly devices on the network.
    #
    logger.info(f'Scanning for Shelly devices for {30} seconds')

    zeroconf = Zeroconf()

    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])

    # We will give the script 30 seconds to find all Shelly devices.
    #
    time.sleep(30)
    
    zeroconf.close()

    print('Scanning is complete!')

    asyncio.run(process())