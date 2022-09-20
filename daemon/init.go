package main

// TODO: sudo modprobe tun
// TODO: expose test
// TODO: add nameserver to /run/resolvconf/resolv.conf
//
// subprocess.run(['/usr/bin/sudo', '-S', 'sed', '-i','1i'+'nameserver '+ dns, '/run/resolvconf/resolv.conf'],
// subprocess.run(['/usr/bin/sudo', '-S', 'resolvconf', '-u'],
import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"os/signal"
	"path"
	"syscall"
	"time"

	"github.com/vishvananda/netlink"
	"golang.zx2c4.com/wireguard/conn"
	"golang.zx2c4.com/wireguard/device"
	"golang.zx2c4.com/wireguard/ipc"
	"golang.zx2c4.com/wireguard/tun"
	"golang.zx2c4.com/wireguard/wgctrl"
	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

var logger *device.Logger

const CONFIG_BASE_PATH = "/home/david"

type userspaceFiles struct {
	dev          *device.Device
	uapiFile     *os.File
	uapiListener net.Listener
}

func configureInterface(iface string, config Config, routeAllTraffic bool) error {
	var cfg wgtypes.Config
	const MAIN_ROUTING_TABLE = 254
	// https://man7.org/linux/man-pages/man8/ip-rule.8.html
	// no need to parse, 254 is defined as main
	const TABLE = 2468
	var FWMARK int = 666

	client, err := wgctrl.New()
	key, err := wgtypes.ParseKey(config.PrivateKey)
	cfg.PrivateKey = &key

	cfg.FirewallMark = &FWMARK
	cfg.Peers = []wgtypes.PeerConfig{}
	for _, p := range config.Peers {
		pubk, _ := wgtypes.ParseKey(p.PublicKey)
		transformed := wgtypes.PeerConfig{PublicKey: pubk,
			Endpoint:                    &net.UDPAddr{IP: p.IP, Port: p.Port},
			PersistentKeepaliveInterval: &p.KeepAliveInterval,
			AllowedIPs:                  p.AllowedIPs}
		cfg.Peers = append(cfg.Peers, transformed)

	}
	err = client.ConfigureDevice(iface, cfg)
	if err != nil {
		return err
	}

	link, err := netlink.LinkByName(iface)
	if err != nil {
		return err
	}

	netlink.LinkSetUp(link)
	addr, _ := netlink.ParseAddr("10.88.88.7/24")
	netlink.AddrAdd(link, addr)
	// this is a terrible hack; the interface being up somehow
	// does not register routes for "a bit"
	// 500ms seems to work on a Nexus 5
	time.Sleep(time.Millisecond * 500)

	if routeAllTraffic {
		// https://www.wireguard.com/netns/#routing-all-your-traffic
		r := netlink.Route{
			Scope: netlink.SCOPE_UNIVERSE,
			Table: TABLE,
			Dst: &net.IPNet{IP: net.IPv4(0, 0, 0, 0),
				Mask: net.CIDRMask(0, 32),
			},
			LinkIndex: link.Attrs().Index,
		}
		err = netlink.RouteAdd(&r)
		fmt.Printf("routeadd %v\n", err)

		found_rules, err := netlink.RuleList(netlink.FAMILY_V4)
		fmt.Printf("rulelist %#v\n", err)
		for _, found_rule := range found_rules {
			fmt.Printf("found rule %#v\n", found_rule)
			if found_rule.Mark == FWMARK && found_rule.Table == TABLE {
				netlink.RuleDel(&found_rule)
			}
			if found_rule.Table == MAIN_ROUTING_TABLE && found_rule.SuppressPrefixlen == 0 {
				netlink.RuleDel(&found_rule)
			}
		}
		rule := netlink.NewRule()
		rule.Invert = true
		rule.Mark = FWMARK
		rule.Table = TABLE
		// TODO configurable exclusions
		// if empty, eats up all traffic
		//_, to_exclude, err := net.ParseCIDR("192.168.0.0/16")
		//rule.Dst = to_exclude

		err = netlink.RuleAdd(rule)
		fmt.Printf("ruleadd %v\n", err)

		defrule := netlink.NewRule()
		defrule.Table = MAIN_ROUTING_TABLE
		defrule.SuppressPrefixlen = 0
		err = netlink.RuleAdd(defrule)
		fmt.Printf("ruleadd2 %v\n", err)
	} else {
		r := netlink.Route{
			Scope: netlink.SCOPE_UNIVERSE,
			Dst: &net.IPNet{IP: net.IPv4(8, 8, 8, 0),
				Mask: net.CIDRMask(24, 32),
				// FIXME
			},
			LinkIndex: link.Attrs().Index,
		}
		err = netlink.RouteAdd(&r)
		fmt.Printf("nonall-ruleadd %v\n", err)

		r2 := netlink.Route{
			Scope: netlink.SCOPE_UNIVERSE,
			Dst: &net.IPNet{IP: net.IPv4(10, 88, 88, 0),
				Mask: net.CIDRMask(24, 32),
			},
			LinkIndex: link.Attrs().Index,
		}
		err = netlink.RouteAdd(&r2)
		fmt.Printf("ruleadd2 %v\n", err)
	}
	return nil
}
func createUserspaceInterface(interfaceName string) (*userspaceFiles, error) {
	tun, err := tun.CreateTUN(interfaceName, device.DefaultMTU)
	if err != nil {
		logger.Errorf("Failed to create TUN device '%s': %s", interfaceName, err)
		return nil, err
	}
	tunDevice := device.NewDevice(tun, conn.NewDefaultBind(), logger)
	logger.Verbosef("Device %s created", interfaceName)
	fileUAPI, err := ipc.UAPIOpen(interfaceName)
	if err != nil {
		logger.Errorf("Failed to open uapi socket: %v", err)
		return nil, err
	}
	uapi, err := ipc.UAPIListen(interfaceName, fileUAPI)
	if err != nil {
		logger.Errorf("Failed to listen on uapi socket: %v", err)
		return nil, err
	}

	go func() {
		for {
			conn, err := uapi.Accept()
			if err != nil {
				logger.Errorf("Got error in uapi Accept: %v", err)
				return
			}
			go tunDevice.IpcHandle(conn)
		}
	}()

	logger.Verbosef("UAPI listener started")
	return &userspaceFiles{dev: tunDevice, uapiFile: fileUAPI, uapiListener: uapi}, nil
}

func createKernelspaceInterface(interfaceName string) error {
	attrs := netlink.NewLinkAttrs()
	attrs.Name = interfaceName
	attrs.Flags = net.FlagUp | net.FlagMulticast | net.FlagPointToPoint
	attrs.TxQLen = 500 // copy userspace values

	err := netlink.LinkAdd(&netlink.Wireguard{
		LinkAttrs: attrs,
	})
	return err
}
func main() {
	interfaceName := "wg0"
	logLevel := device.LogLevelVerbose
	logger = device.NewLogger(
		logLevel,
		fmt.Sprintf("(%s) ", interfaceName),
	)
	// TODO: refuse to run if not setuid / root?

	// TODO log to .cache/wireguard.davidv.dev/daemon.log
	// TODO log to .cache/wireguard.davidv.dev/daemon-<profile>.log
	daemonize := false

	for _, val := range os.Args[1:] {
		switch val {
		case "--daemonize":
			daemonize = true
		default:
			logger.Errorf("Unknown argument %s; try --daemonize", val)
			return
		}
	}

	if daemonize {
		var newArgs []string
		for _, arg := range os.Args[1:] {
			if arg != "--daemonize" {
				newArgs = append(newArgs, arg)
			}
		}

		syscall.Setsid()
		syscall.Chdir("/")
		signal.Ignore(syscall.SIGCHLD)
		syscall.Close(0)
		syscall.Close(1)
		syscall.Close(2)

		cmd := exec.Command(os.Args[0], newArgs...)
		cmd.Start()
		os.Exit(0)
	}

	RPCServer()

}

func disconnect(interfaceName string) error {
	link, err := netlink.LinkByName(interfaceName)
	if err != nil {
		return err
	}

	err = netlink.LinkDel(link)
	if err != nil {
		return err
	}
	return nil
}

func connect(useUserspace bool, interfaceName string, routeAllTraffic bool) {
	cfg, err := parseConfig(path.Join(CONFIG_BASE_PATH, fmt.Sprintf("%s.conf", interfaceName)))
	if err != nil {
		logger.Errorf("Failed to parse interface %s: %s", interfaceName, err)
		return
	}
	_ = disconnect(interfaceName)
	if useUserspace {
		uFiles, err := createUserspaceInterface(interfaceName)
		if err != nil {
			logger.Errorf("Failed to create interface %s: %s", interfaceName, err)
			return
		}
		logger.Verbosef("Interface %s created (userspace)", interfaceName)
		err = configureInterface(interfaceName, *cfg, routeAllTraffic)
		if err != nil {
			logger.Errorf("Failed to configure interface %s: %s", interfaceName, err)
			return
		}
		logger.Verbosef("Interface %s configured (userspace), waiting for it to be deleted", interfaceName)
		go func() {
			<-uFiles.dev.Wait()
			uFiles.dev.Close()
			uFiles.uapiListener.Close()
			uFiles.uapiFile.Close()
		}()
	} else {
		err := createKernelspaceInterface(interfaceName)
		if err != nil && err != syscall.EEXIST {
			logger.Errorf("Failed to create Kernelspace interface: %s", err)
			return
		}
		logger.Verbosef("Interface %s created (kernel)", interfaceName)
		err = configureInterface(interfaceName, *cfg, routeAllTraffic)
		if err != nil {
			logger.Errorf("Failed to configure interface %s: %s", interfaceName, err)
			return
		}
		logger.Verbosef("Interface %s configured (kernel), exiting", interfaceName)
	}
}
