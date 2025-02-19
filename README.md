# Shelly Detached Mode Watchdog AKA The Shelly Failsafe

This project provides a failsafe solution for Shelly1 relays using a button type of `detached`

I have several Shelly1 relays in `Detached` mode, powering smart bulbs. I use `Node-RED` to listen for changes in the status of the Shelly Input, which then toggles the status of the smart bulb. This gives me the best of both worlds since I can continue using the physical switch and operate the smart bulb from my phone/Home Assistant etc. without worrying about it being switched off.

The danger with this approach is that a failure in NodeRED or HomeAssistant would mean I couldn't operate any of the light. To help mitigate this, I created this watchdog script that is connected to Home Assistant. If the script loses connection to Home Assistant, it will put all the Shelly1 devices back into the standard `toggle` mode, which restores the physical light switch control.

I call this the `Shelly Failsafe`.

> [!NOTE]
> This failsafe is only for Shelly1 Gen1 relays as they don't support their own scripts.

> [!NOTE]
> The scripts assume the Shelly HTTP API has no authentication required.

# Usage

> [!NOTE]
> These instructions assume your running the scripts on Linux

Start by execute the `setup.py` script. This will locate all `Shelly1` devices with a `detached` relay.

```
python setup.py
```

Once the scan is complete, you will have a `setup.json` file.

Before starting the watchdog, you must provide configuration so it can connect to HomeAssistant. Create a `.env` file using the `.env_template`

```
cp .env_template .env
```

Replace the values in the angled brackets so it looks something like this:

```
HOME_ASSISTANT_WEBSOCKET_HOST=192.1.1.12
HOME_ASSISTANT_WEBSOCKET_PORT=8124
HOME_ASSISTANT_WEBSOCKET_TOKEN=AAA...BBB
```

You can then start the watchdog. I use `nohup` to run the script in the background.

```
chmod +x watchdog.py

nohup python watchdog.py &
```

## setup.py

The first script to execute is `setup.py`. This will use mDNS to locate all Shelly1 devices on the local network.

Once they are located, it will make an indivial HTTP request to the `/settings/relay/0` endpoint to get the current value for `btn_type`. If this value is `detached`, the name of the device is recorded.

Once this script has finished running, you will have a `setup.json` file. It should look something like this

```
{
    "detached_shellys": [
        "shelly1-40F52000342F._http._tcp.local."
    ]
}
```

## watchdog.py

This is the primary script. It will open a WebSocket connection to your Home Assistant. If this connection is severed for any reason, it will execute the `failsafe`. Once connectivity to Home Assistant is restored, the `restore` process will be executed.

> [!TIP]
> If you perform a reboot of Home Assistant, the failsafe will activate. If might be worth stopping the watchdog if you are doing planned maintenance.

## failsafe.py

This script contains the code that will actually switch the relays from detached to toggle. It's provided so you can test it works and manually execute it if required.

Once you have generated the setup.json file using `setup.py`, you can execute failsafe.py. This will use mDNS to get the IP Address for each of the Shelly devices listed in the `setup.json` file. It will then 
use the HTTP API to update the relay configuration.

## restore.py

This script essentially reverses the failsafe and will set the `btn_type` to `detached` for all the relays in the `setup.json` file. Like `failsafe.py`, this script is provided so you can test it and manually execute it.

