# Wireguard

Wireguard VPN. 

Supports kernel & fallback userspace implementation. The userspace implementation is **alpha quality**. The kernel implementation is very solid.

How to use:

* Add a new profile
* On the main screen, tap on the profile to connect/disconnect.

Features:

* Multiple profiles
  * they can all be enabled at the same time
* Userspace fallback
* Extra routes can be added per-profle

## Screenshots
![](https://github.com/davidventura/wireguard_qml/blob/master/screenshots/main.png?raw=true)
![](https://github.com/davidventura/wireguard_qml/blob/master/screenshots/create_profile.png?raw=true)

## Get kernel support for wireguard on your device

It is very easy! You can follow the steps [here](https://www.wireguard.com/compilation/) and send a MR to your maintainer.  
If you don't feel up to the task, open an issue and fill in the template

### Instructions to build the kernel module

1. Find your kernel sources, probably [here](https://gitlab.com/ubports), and clone them
2. In the sources, run something like `/usr/bin/make  O=../kernel-out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabihf-  modules_prepare -j$(nproc)`
3. Clone [wireguard](https://github.com/WireGuard/wireguard-linux-compat) kernel sources
4. Run `make -C src -j$(nproc) KERNELDIR=<PATH>/kernel-out/ ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabihf- module`
5. Try to load the resulting `wireguard.ko` on your device: `sudo insmod wireguard.ko`


## Logs

Userspace daemon to update routes is at `~/.cache/wireguard.davidv.dev/daemon-de.log`.  
Userspace wireguard daemon is at `~/.cache/wireguard.davidv.dev/daemon-de.log/boring.log`.  

## License

Copyright (C) 2021  David Ventura

Licensed under the MIT license
