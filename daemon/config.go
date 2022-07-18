package main

import (
	"errors"
	"fmt"
	"net"
	"strconv"
	"strings"
	"time"

	"github.com/go-ini/ini"
)

type Peer struct {
	IP                net.IP
	Port              int
	PublicKey         string
	AllowedIPs        []net.IPNet
	KeepAliveInterval time.Duration
}
type Config struct {
	InterfaceName string
	TunnelName    string
	Address       net.IP
	MaskLen       int
	PrivateKey    string
	Peers         []Peer
}

func parseConfig(path string) (*Config, error) {
	cfg, err := ini.LoadSources(
		ini.LoadOptions{
			AllowNonUniqueSections: true,
		},
		path,
	)
	if err != nil {
		return nil, err
	}

	var peers []Peer
	sects, err := cfg.SectionsByName("Peer")
	if err != nil {
		return nil, err
	}
	for _, sec := range sects {
		prefixes := strings.Split(sec.Key("AllowedIPs").String(), ",")
		var cidrs []net.IPNet
		for _, p := range prefixes {
			_, net, err := net.ParseCIDR(strings.Trim(p, " "))
			if err != nil {
				return nil, err
			}

			cidrs = append(cidrs, *net)
		}

		endpoint := strings.SplitN(sec.Key("Endpoint").String(), ":", 2)
		endpoint_addr, err := net.LookupIP(endpoint[0])
		if err != nil {
			return nil, err
		}
		endpoint_port, err := strconv.Atoi(endpoint[1])
		if err != nil {
			return nil, err
		}
		if len(endpoint_addr) == 0 {
			return nil, errors.New("Could not resolve")
		}

		keepalive_interval := time.Second * 0
		if sec.HasKey("KeepAliveInterval") {
			interval, err := strconv.Atoi(sec.Key("KeepAliveInterval").String())
			if err != nil {
				logger.Errorf("Failed to parse KeepAliveInterval for Peer %s: %s", endpoint_addr[0], err)
			} else {
				keepalive_interval = time.Duration(interval) * time.Second
			}
		}
		p := Peer{
			IP:                endpoint_addr[0],
			Port:              endpoint_port,
			PublicKey:         sec.Key("PublicKey").String(),
			AllowedIPs:        cidrs,
			KeepAliveInterval: keepalive_interval,
		}
		peers = append(peers, p)
	}

	sec, err := cfg.GetSection("Interface")
	if err != nil {
		return nil, err
	}
	addr, net, err := net.ParseCIDR(sec.Key("Address").String())
	if err != nil {
		return nil, err
	}
	masklen, _ := net.Mask.Size()
	c := Config{
		TunnelName: sec.Key("TunnelName").String(),
		Address:    addr,
		MaskLen:    masklen,
		PrivateKey: sec.Key("PrivateKey").String(),
		Peers:      peers,
	}
	fmt.Printf("%+v\n", c)
	return &c, nil
}