from dotenv import load_dotenv
from aiohttp import ClientSession, ClientWebSocketResponse
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
from failsafe import initiate_failsafe
from restore import initiate_restore
import logging
import os
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("watchdog")

safeguard_active = False

async def subscribe_to_messages(websocket: ClientWebSocketResponse) -> None:
    async for message in websocket:
        if isinstance(message, WSMessage):
            if message.type == WSMsgType.text:
                message_json = message.json()
                if message_json.get("type") == "auth_required":
                    logger.info("> Auth request from server received: %s", message_json)
                    homeassistant_token = os.getenv("HOME_ASSISTANT_WEBSOCKET_TOKEN")
                    await websocket.send_json({"type": "auth", "access_token": homeassistant_token})
                elif message_json.get("type") == "auth_ok":
                    logger.info("> Auth success from server received: %s", message_json)
                    await initiate_restore()
                else:
                    logger.info("> Message from server received: %s", message_json)

async def handler() -> None:

    logger.info("> Connecting to Home Assistant")

    homeassistant_host = os.getenv("HOME_ASSISTANT_WEBSOCKET_HOST")
    homeassistant_port = os.getenv("HOME_ASSISTANT_WEBSOCKET_PORT")

    url = f"ws://{homeassistant_host}:{homeassistant_port}/api/websocket"

    while(True):
        logger.info("> Connecting to Home Assistant")

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
                        logger.info("> Abnormal disconnect from server")

                    logger.info("Initiating Safeguard...")

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
        
if __name__ == "__main__":
    load_dotenv()

    print("Shelly Failsafe Watchdog is running!")

    asyncio.run(handler())