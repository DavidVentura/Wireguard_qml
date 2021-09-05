import QtQuick 2.0
import Ubuntu.Components 1.3 as UITK
import io.thp.pyotherside 1.3
import Qt.labs.settings 1.0

import "../components"

UITK.Page {
    Settings {
        id: settings
        property bool useUserspace: false
    }
    header: UITK.PageHeader {
        id: header
        title: "Wireguard"
        trailingActionBar.actions: [
            UITK.Action {
                iconName: "add"
                onTriggered: {
                    stack.push(Qt.resolvedUrl("ProfilePage.qml"))
                }
            }
        ]
    }
    ListView {
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        spacing: units.gu(0.1)

        id: lv
        model: ListModel {
            id: listmodel
            dynamicRoles: true
        }

        delegate: UITK.ListItem {
            height: units.gu(10)
            trailingActions: UITK.ListItemActions {
                actions: [
                    UITK.Action {
                        iconName: 'edit'
                        onTriggered: {
                            stack.push(Qt.resolvedUrl("ProfilePage.qml"), {
                                           "isEditing": true,
                                           "profileName": profile_name,
                                           "peers": peers,
                                           "ipAddress": ip_address,
                                           "privateKey": private_key,
                                           "extraRoutes": extra_routes,
                                           "interfaceName": interface_name
                                       })
                        }
                    },
                    UITK.Action {
                        iconName: 'webbrowser-app'
                        visible: !status
                        onTriggered: {
                            python.call('vpn._connect',
                                        [profile_name, !settings.useUserspace],
                                        function (error_msg) {
                                            if (error_msg) {
                                                toast.show('Failed:' + error_msg)
                                                return
                                            }
                                            toast.show('Connected')
                                        })
                        }
                    },
                    UITK.Action {
                        iconName: "close"
                        visible: status
                        onTriggered: {
                            python.call('vpn.interface.disconnect',
                                        [interface_name], function () {
                                            toast.show("Disconnected")
                                        })
                        }
                    }
                ]
            }
            Column {
                anchors.leftMargin: units.gu(2)
                anchors.rightMargin: units.gu(2)
                anchors.left: parent.left
                anchors.right: parent.right

                Text {
                    text: interface_name + ' - ' + profile_name
                }

                Repeater {
                    visible: status
                    model: status.peers
                    anchors.left: parent.left
                    anchors.right: parent.right
                    delegate: Text {
                        text: peerName(status.peers[index].public_key,
                                       peers) + ' RX: ' + toHuman(
                                  status.peers[index].rx) + ' TX: ' + toHuman(
                                  status.peers[index].tx) + ' Up for: ' + ago(
                                  status.peers[index].latest_handshake)
                    }
                }
            }
        }
    }

    Timer {
        repeat: true
        interval: 1000
        running: true
        onTriggered: {
            showStatus()
        }
    }

    function peerName(pubkey, peers) {
        for (var i = 0; i < peers.count; i++) {
            const peer = peers.get(i)
            if (peer.key === pubkey) {
                return peer.name
            }
        }
        return 'unknown peer'
    }
    function ago(ts) {
        const delta = (new Date().getTime()) / 1000 - ts
        if (delta > 3600) {
            return Math.round(delta / 3600) + 'h'
        }
        if (delta > 60) {
            return Math.round(delta / 60) + 'm'
        }
        if (delta < 60) {
            return Math.round(delta) + 's'
        }
    }

    function toHuman(q) {
        if (!q) {
            return 0
        }

        const units = ['B', 'KB', 'MB', 'GB', 'TB']
        let i = 0
        while (q > 1024) {
            q = q / 1024
            i++
        }
        return Math.round(q, 1) + units[i]
    }

    function populateProfiles() {
        python.call('vpn.list_profiles', [], function (profiles) {
            listmodel.clear()
            for (var i = 0; i < profiles.length; i++) {
                listmodel.append(profiles[i])
            }
        })
    }
    function showStatus() {
        python.call('vpn.interface.current_status_by_interface', [],
                    function (all_status) {
                        const keys = Object.keys(all_status)
                        for (var i = 0; i < listmodel.count; i++) {
                            const entry = listmodel.get(i)

                            let status = ''
                            for (const idx in Object.keys(all_status)) {
                                const key = keys[idx]
                                const i_status = all_status[key]
                                if (entry.interface_name === key) {
                                    status = i_status
                                    break
                                }
                            }
                            listmodel.setProperty(i, 'status', status)
                        }
                    })
    }

    Python {
        id: python
        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl('../../src/'))
            importModule('vpn', function () {
                populateProfiles()
                showStatus()
            })
        }
    }
}
