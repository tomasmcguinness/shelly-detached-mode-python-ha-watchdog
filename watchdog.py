from dotenv import load_dotenv
from aiohttp import ClientSession, ClientWebSocketResponse
from aiohttp.http_websocket import WSMessage
from aiohttp.web import WSMsgType
from failsafe import initiate_failsafe
from restore import initiate_restore
import logging
import os
import asyncio

is_failsafe_active = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("watchdog")

async def subscribe_to_messages(websocket: ClientWebSocketResponse) -> None:

    global is_failsafe_active

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
                    logger.info("> Connected to HomeAssistant! ")

                    if is_failsafe_active:
                        logger.info("> Failsafe was previoulsy activated so initiate restore...")
                        await initiate_restore()
                        is_failsafe_active = False
                        logger.info("> Restore completed successfully. Failsafe is no longer active.")
                else:
                    logger.info("> Message from server received: %s", message_json)

async def handler() -> None:

    global is_failsafe_active

    homeassistant_host = os.getenv("HOME_ASSISTANT_WEBSOCKET_HOST")
    homeassistant_port = os.getenv("HOME_ASSISTANT_WEBSOCKET_PORT")

    url = f"ws://{homeassistant_host}:{homeassistant_port}/api/websocket"

    while(True):
        logger.info("> Connecting to Home Assistant...")

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
                    logger.warning(f"> Websocket connection closed with code {ws.close_code}")

                    if ws.close_code == 1006:
                        logger.info("> Abnormal disconnect from server")

                    logger.info("> Initiating Failsafe...")

                    is_failsafe_active = True

                    await initiate_failsafe()

                    logger.info("> Failsafe has been activated. Attempting to reconnect HomeAssistant...")

                    # First, we want to close the websocket connection if it's not closed by some other function above
                    if not ws.closed:
                        await ws.close()
                    # Then, we cancel each task which is pending:
                    for task in pending:
                        task.cancel()
                    # At this point, everything is shut down. The program will exit.
        except Exception as e:
            logger.error(f"> {e}")
        
if __name__ == "__main__":

    load_dotenv()

    logger.info("> Shelly Failsafe Watchdog is starting...")

    asyncio.run(handler())