from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from dotenv import load_dotenv
from aiohttp import ClientSession, ClientWebSocketResponse
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType

import logging
import os
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('client')

async def subscribe_to_messages(websocket: ClientWebSocketResponse) -> None:
    async for message in websocket:
        if isinstance(message, WSMessage):
            if message.type == WSMsgType.text:
                message_json = message.json()
                if message_json.get('action') == 'chat_message' and not message_json.get('success'):
                    print(f'>>>{message_json["user"]}: {message_json["message"]}')
                logger.info('> Message from server received: %s', message_json)

async def handler() -> None:

    homeassistant_host = os.getenv("HOME_ASSISTANT_WEBSOCKET_HOST")
    homeassistant_port = os.getenv("HOME_ASSISTANT_WEBSOCKET_PORT")

    url = 'ws://{}:{}/api/websocket'.format(homeassistant_host, homeassistant_port)

    async with ClientSession() as session:
        async with session.ws_connect(url, ssl=False) as ws:

            read_message_task = asyncio.create_task(subscribe_to_messages(websocket=ws))
            
            done, pending = await asyncio.wait(
                [read_message_task], #ping_task, send_input_message_task], 
                return_when=asyncio.FIRST_COMPLETED,
            )

            # First, we want to close the websocket connection if it's not closed by some other function above
            if not ws.closed:
                await ws.close()
            # Then, we cancel each task which is pending:
            for task in pending:
                task.cancel()
            # At this point, everything is shut down. The program will exit.

if __name__ == '__main__':
    load_dotenv()
    asyncio.run(handler())


# async def initSocket():

#     homeassistant_host = os.getenv("HOME_ASSISTANT_WEBSOCKET_HOST")
#     homeassistant_port = os.getenv("HOME_ASSISTANT_WEBSOCKET_PORT")
#     homeassistant_token = os.getenv("HOME_ASSISTANT_WEBSOCKET_TOKEN")

#     websocket = await asyncws.connect('ws://{}:{}/api/websocket'.format(homeassistant_host, homeassistant_port))

#     await websocket.send(json.dumps({'type': 'auth','access_token': homeassistant_token}))
#     await websocket.send(json.dumps({'id': 1, 'type': 'subscribe_events', 'event_type': 'state_changed'}))
    
#     print("Start socket...")

#     while True:
#         message = await websocket.recv()
#         if message is None:
#             break
        
#         try:   
#             data = json.loads(message)['event']['data']
#             entity_id = data['entity_id']

#             print(entity_id)
            
#             # if entity_id in entities:
                
#             #     print("writing {} to cache".format(entity_id))
                
#             #     if 'unit_of_measurement' in data['new_state']['attributes']:
#             #         cache[entity_id] = "{} {}".format(data['new_state']['state'], data['new_state']['attributes']['unit_of_measurement'])
#             #     else:
#             #         cache[entity_id] = data['new_state']['state']
                    
#         except Exception:
#             pass

# async def main():
#     load_dotenv()

#     listen = asyncio.create_task(initSocket()) 

#     await listen

# if __name__ == "__main__":
#     asyncio.run(main())

# def on_service_state_change(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
#     print(f"Service {name} of type {service_type} state changed: {state_change}")

#     if state_change is ServiceStateChange.Added:
#         info = zeroconf.get_service_info(service_type, name)
#         print(f"Info from zeroconf.get_service_info: {info!r}")

#         if info:
#             addresses = [f"{addr}:{cast(int, info.port)}" for addr in info.parsed_scoped_addresses()]
#             print(f"  Addresses: {', '.join(addresses)}")
#             print(f"  Weight: {info.weight}, priority: {info.priority}")
#             print(f"  Server: {info.server}")
#             if info.properties:
#                 print("  Properties are:")
#                 for key, value in info.properties.items():
#                     print(f"    {key!r}: {value!r}")
#             else:
#                 print("  No properties")
#         else:
#             print("  No info")
#         print("\n")

# def on_close(ws):
#     print("Disconnected from server")
#     print("Retry : %s" % time.ctime())

#     time.sleep(10)
#     connect_to_homeassistant() # retry per 10 seconds

#     # If we fail three times to reconnect, initial the "safe-guard"
#     #

# def on_open(ws):
#     print('connection established')

# def on_message(ws, message):
#     print(message)

# def main():

#     load_dotenv()

#     # Using mDNS, find all Shelly devices on the network.
#     #
#     print(f'Scanning for Shelly devices for {30} seconds')

#     # zeroconf = Zeroconf()

#     # browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change])

#     # # We will give the script 30 seconds to find all Shelly devices.
#     # #
#     # time.sleep(30000)
    
#     # zeroconf.close()

#     # With a list of all Shelly Devices in memory, open a channel to Home Assistant.
#     #
#     # try:
#     #     #connect_to_homeassistant()
#     # except Exception as err:
#     #     print(err)
#     #     print("Connection failed")

# if __name__ == "__main__":
    
#     load_dotenv()

#     print("Connecting to Home Assistant")

#     # Fetch the Home Assistant websocket host and key from the environment.
#     #
#     homeassistant_host = os.getenv("HOME_ASSISTANT_WEBSOCKET_HOST")
#     homeassistant_token = os.getenv("HOME_ASSISTANT_WEBSOCKET_TOKEN")

#     url = "ws://{}".format(homeassistant_host)

#     ws = websocket.WebSocketApp(url, on_open = on_open, on_close = on_close, on_message=on_message)

#     wst = threading.Thread(target=ws.run_forever)
#     wst.daemon = True
#     wst.start()
    
