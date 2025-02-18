from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from dotenv import load_dotenv
from aiohttp import ClientSession, ClientWebSocketResponse
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
from typing import cast
import time
import logging
import os
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('client')

failsave_active = False

def on_service_state_change(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
    #print(f"Service {name} of type {service_type} state changed: {state_change}")

    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        #print(f"Info from zeroconf.get_service_info: {info!r}")

        if info:
            addresses = [f"{addr}:{cast(int, info.port)}" for addr in info.parsed_scoped_addresses()]
            print(f"  Addresses: {', '.join(addresses)}")
            # print(f"  Weight: {info.weight}, priority: {info.priority}")
            # print(f"  Server: {info.server}")
            # if info.properties:
            #     print("  Properties are:")
            #     for key, value in info.properties.items():
            #         print(f"    {key!r}: {value!r}")
            # else:
            #     print("  No properties")

            # Make an API request to the Shelly Device to check its version.
            #

            # async with aiohttp.ClientSession() as session:
            #     async with session.get('http://httpbin.org/get') as resp:
            #         print(resp.status)
            #         print(await resp.text())

        else:
            print("  No info")
     #   print("\n")

async def initiate_failsafe() -> None:
    logger.info('> Initiating failsafe')

async def restore_behaviour() -> None:
    logger.info('> Restore behaviour')

async def subscribe_to_messages(websocket: ClientWebSocketResponse) -> None:
    async for message in websocket:
        if isinstance(message, WSMessage):
            if message.type == WSMsgType.text:
                message_json = message.json()
                if message_json.get('type') == 'auth_required':
                    logger.info('> Auth request from server received: %s', message_json)
                    homeassistant_token = os.getenv("HOME_ASSISTANT_WEBSOCKET_TOKEN")
                    await websocket.send_json({'type': 'auth', 'access_token': homeassistant_token})
                elif message_json.get('type') == 'auth_ok':
                    logger.info('> Auth success from server received: %s', message_json)
                    await restore_behaviour()
                else:
                    logger.info('> Message from server received: %s', message_json)

async def handler() -> None:

    homeassistant_host = os.getenv("HOME_ASSISTANT_WEBSOCKET_HOST")
    homeassistant_port = os.getenv("HOME_ASSISTANT_WEBSOCKET_PORT")

    url = 'ws://{}:{}/api/websocket'.format(homeassistant_host, homeassistant_port)

    while(True):
        logger.info('> Connecting to Home Assistant')

        try:
            async with ClientSession() as session:

                async with session.ws_connect(url, ssl=False) as ws:

                    read_message_task = asyncio.create_task(subscribe_to_messages(websocket=ws))
                    
                    done, pending = await asyncio.wait(
                        [read_message_task], #ping_task, send_input_message_task], 
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # Connection to HomeAssistant has been lost.
                    #

                    logger.info(ws.close_code)

                    if ws.close_code == 1006:
                        logger.info('> Abnormal disconnect from server')

                    await initiate_failsafe()

                    # First, we want to close the websocket connection if it's not closed by some other function above
                    if not ws.closed:
                        await ws.close()
                    # Then, we cancel each task which is pending:
                    for task in pending:
                        task.cancel()
                    # At this point, everything is shut down. The program will exit.
        except Exception as e:
            logger.error(e)
        
if __name__ == '__main__':
    load_dotenv()

    # Using mDNS, find all Shelly devices on the network.
    #
    print(f'Scanning for Shelly devices for {30} seconds')

    zeroconf = Zeroconf()

    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])

    # We will give the script 30 seconds to find all Shelly devices.
    #
    time.sleep(30)
    
    zeroconf.close()

    print('Scanning is complete!')

    asyncio.run(handler())