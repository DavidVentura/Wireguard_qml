package main

import (
	"encoding/json"
	"net/http"
	"time"

	"golang.zx2c4.com/wireguard/wgctrl"
	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

const peerStatusPath = "/peer_status/"
const genKeyPairPath = "/generate_key_pair/"
const connectPath = "/connect/"
const disconnectPath = "/disconnect/"

type badRequest struct {
	Err string `json:"error"`
}

type peerStatusResponse struct {
	Endpoint      string
	ReceiveBytes  int64
	TransmitBytes int64
	Seen          bool
}

type keyPairResponse struct {
	Private string
	Public  string
}

func generateKeyPair(w http.ResponseWriter, r *http.Request) {
	privk, _ := wgtypes.GeneratePrivateKey()
	pubk := privk.PublicKey()
	encoder := json.NewEncoder(w)
	w.Header().Set("Content-Type", "application/json")
	encoder.Encode(keyPairResponse{Private: privk.String(), Public: pubk.String()})
}

func peerStatus(w http.ResponseWriter, r *http.Request) {
	interfaceName := r.URL.Path[len(peerStatusPath):]
	encoder := json.NewEncoder(w)
	w.Header().Set("Content-Type", "application/json")

	c, err := wgctrl.New()
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		encoder.Encode(badRequest{Err: err.Error()})
		return
	}
	dev, err := c.Device(interfaceName)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		encoder.Encode(badRequest{Err: err.Error()})
		return
	}
	var peers []peerStatusResponse

	for _, peer := range dev.Peers {
		peers = append(peers, peerStatusResponse{
			Endpoint:      peer.Endpoint.String(),
			ReceiveBytes:  peer.ReceiveBytes,
			TransmitBytes: peer.TransmitBytes,
			Seen:          peer.LastHandshakeTime != time.Time{},
		})
	}
	encoder.Encode(peers)
}

func connectTunnel(w http.ResponseWriter, r *http.Request) {
	tunnelName := r.URL.Path[len(connectPath):]
	logger.Verbosef("Requested to bring up %s\n", tunnelName)
	connect(false, "wg0", false)
	w.WriteHeader(http.StatusNoContent)
}

func disconnectTunnel(w http.ResponseWriter, r *http.Request) {
	tunnelName := r.URL.Path[len(connectPath):]
	logger.Verbosef("Requested to bring down %s\n", tunnelName)
	err := disconnect("wg0")
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(badRequest{Err: err.Error()})
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func RPCServer() error {
	http.HandleFunc(peerStatusPath, peerStatus)
	http.HandleFunc(genKeyPairPath, generateKeyPair)
	http.HandleFunc(connectPath, connectTunnel)
	http.HandleFunc(disconnectPath, disconnectTunnel)
	logger.Verbosef("Bringing up HTTP server\n")
	return http.ListenAndServe("127.0.0.1:12345", nil)
}
