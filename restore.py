from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from typing import cast
from aiohttp import ClientSession
from shelly import Shelly
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("restore")

requested_device_names = []
discovered_devices = []

def on_service_state_change(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:

    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)

        if info.name in requested_device_names:
            if info:
                addresses = [f"{addr}:{cast(int, info.port)}" for addr in info.parsed_scoped_addresses()]
                discovered_devices.append(Shelly(name, addresses[0]))
                logger.info(f"> Shelly1 [{name}] resolved to [{addresses[0]}]")   

async def initiate_restore() -> None:

    logger.info("> Resolving IP addresses for Shelly devices!")

    with open("setup.json") as f:
        data = json.load(f)
        f.close()

        detached_shellys = data["detached_shellys"]

        for detached_shelly_name in detached_shellys:
            requested_device_names.append(detached_shelly_name)

        zeroconf = Zeroconf()

        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])

        await asyncio.sleep(30)

        zeroconf.close()

        async with ClientSession() as session:  
            for discovered_device in discovered_devices:

                try:
                    logger.info(f"> Setting btn_type to detached for [{discovered_device.name}]")

                    response = await session.post(url=f"http://{discovered_device.address}/settings/relay/0?btn_type=detached")
                    logger.info(f"> Status: {response.status == 200}")

                    logger.info(f"> Setting relay on for [{discovered_device.name}]")

                    response = await session.post(url=f"http://{discovered_device.address}/relay/0?turn=on")
                    logger.info(f"> Status: {response.status == 200}")
                            
                except Exception as e:
                    logger.error(e)

            logger.info("> Finished updating btn_type to detached and switching relays on")

if __name__ == "__main__":
    logger.info("> Restore has started...")
    asyncio.run(initiate_restore())
    
