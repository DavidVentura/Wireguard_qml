# Wireguard

Wireguard VPN. 

Supports kernel & fallback userspace implementation. The userspace implementation is **alpha quality**. The kernel implementation is very solid.

## Get kernel support for wireguard on your device

It is very easy! You can follow the steps [here](https://www.wireguard.com/compilation/) and send a MR to your maintainer.  
If you don't feel up to the task, open an issue and fill in the template

## Screenshots
![](https://github.com/davidventura/wireguard_qml/blob/master/screenshots/main.png?raw=true)
![](https://github.com/davidventura/wireguard_qml/blob/master/screenshots/create_profile.png?raw=true)

## Logs

Userspace daemon to update routes is at `~/.cache/wireguard.davidv.dev/daemon-de.log`.  
Userspace wireguard daemon is at `~/.cache/wireguard.davidv.dev/daemon-de.log/boring.log`.  

## License

Copyright (C) 2021  David Ventura

Licensed under the MIT license
