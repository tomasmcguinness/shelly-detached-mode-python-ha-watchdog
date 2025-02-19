from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from aiohttp import ClientSession
import time
import logging
import asyncio
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('client')

failsave_active = False

discovered_devices = []

def on_service_state_change(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
    if state_change is ServiceStateChange.Added:
        if name.startswith("shelly1"):
            logger.info("Found a Shelly1")
            discovered_devices.append(name)

async def process() -> None:

    logger.info(f'Processing {discovered_devices.count} Shelly1 devices')

    with open('setup.json', 'w') as f:

        shellys = {"detached_shellys":[]}

        shellys_holder = shellys["detached_shellys"]

        async with ClientSession() as session:
            for device in discovered_devices:
                try:
                    async with session.get(f'http://{device.address}/settings/relay/0') as resp:
                        logger.info(f'Connected to {device.name}: {resp.status}')
                        data = await resp.json()
                        btn_type = data["btn_type"]

                        if btn_type == 'detached':
                            logger.info(f'Shelly1 {device.name} is in detached mode. Adding to setup.json')
                            shellys_holder.append(device.name)
                            
                except Exception as e:
                    logger.error(e)

        json.dump(shellys, f)
        f.close()

        logger.info('Setup is complete. The setup.json contains a list of all Shelly1 relays in detached mode. You can now run failsafe.py or start watchdog.py.')

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