package main

import (
	"encoding/json"
	"net/http"

	"golang.zx2c4.com/wireguard/wgctrl"
)

const peerStatusPath = "/peer_status/"

type badRequest struct {
	Err string `json:"error"`
}

type peerStatusResponse struct {
	Endpoint      string
	ReceiveBytes  int64
	TransmitBytes int64
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
		peers = append(peers, peerStatusResponse{Endpoint: peer.Endpoint.String(), ReceiveBytes: peer.ReceiveBytes, TransmitBytes: peer.TransmitBytes})
	}
	encoder.Encode(peers)
}

func RPCServer() error {
	http.HandleFunc(peerStatusPath, peerStatus)
	return http.ListenAndServe("127.0.0.1:12345", nil)
}
