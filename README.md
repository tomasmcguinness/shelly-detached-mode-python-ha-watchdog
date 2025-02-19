# Shelly Detached Mode Watchdog AKA The Shelly Safeguard

This project is aimed at providing a failsafe for Shelly1 relays using a button type of `Detached`

I have several Shelly1 relays in `Detached` mode, powering smart bulbs. I use `NodeRED` to listen for changes in the status of the Shelly Input, which then toggles the status of the smart bulb. This gives me the best of both worlds since I can continue using the physical switch and operate the smart bulb from my phone/Home Assistant etc. without worrying about it being switched off.

The danger with this approach is that a failure in NodeRED or HomeAssistant would mean I couldn't operate any of the light. To help mitigate this, I created this watchdog script that is connected to Home Assistant. If the script loses connection to Home Assistant, it will put all the Shelly1 devices back into the standard `toggle` mode, which restores the physical light switch control.

I call this the Shelly Safeguard, after the SILO tv show.

> [!NOTE]
> This failsafe is only for Shelly1 Gen1 relays as they don't support their own scripts.

> [!NOTE]
> The scripts assume the Shelly HTTP API has no authentication required.

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
 
## failsafe.py

This script contains the code that will actually switch the relay from detached to toggle.

Once you have generated the setup.json file using `setup.py`, you can execute failsafe.py. This will use mDNS to get the IP Address for each of the Shelly devices listed in the `setup.json` file. It will then 
use the HTTP API to update the relay configuration.

## restore.py

This script will set the `btn_type` to `detached` for all the relays in the `setup.json` file.