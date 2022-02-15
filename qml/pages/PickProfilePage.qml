import QtQuick 2.0
import QtQuick.Layouts 1.12
import Ubuntu.Components 1.3 as UITK
import io.thp.pyotherside 1.3
import Qt.labs.settings 1.0

import "../components"

UITK.Page {
    Settings {
        id: settings
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
            },
            UITK.Action {
                iconName: "settings"
                onTriggered: {
                    stack.push(Qt.resolvedUrl("SettingsPage.qml"))
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
            height: col.height + col.anchors.topMargin + col.anchors.bottomMargin
            onClicked: {
                if (!c_status.init) {
                    python.call('vpn.instance._connect',
                                [profile_name, !settings.value('useUserspace',
                                                               true)],
                                function (error_msg) {
                                    if (error_msg) {
                                        toast.show('Failed:' + error_msg)
                                        return
                                    }
                                    toast.show('Connecting..')
                                    showStatus()
                                })
                } else {
                    python.call('vpn.instance.interface.disconnect', [interface_name],
                                function () {
                                    toast.show("Disconnected")
                                })
                }
            }

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
                    }
                ]
            }

            Column {
                id: col
                anchors.top: parent.top
                anchors.margins: units.gu(2)
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: units.gu(1)

                RowLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    Text {
                        Layout.fillWidth: true
                        id: prof_name
                        text: profile_name
                        font.pixelSize: units.gu(2.25)
                        font.bold: true
                        color: theme.palette.normal.foregroundText
                    }
                    TunnelStatus {
                        id: ts
                        connected: !!c_status.peers
                        size: 2
                    }
                }
                Item {
                    height: 1
                    anchors.left: parent.left
                    anchors.right: parent.right
                }

                Rectangle {
                    visible: c_status && !!c_status.init
                    height: 1
                    color: theme.palette.normal.backgroundTertiaryText
                    anchors.left: parent.left
                    anchors.right: parent.right
                }

                Repeater {
                    visible: c_status && !!c_status.init
                    model: c_status.peers
                    anchors.left: parent.left
                    anchors.right: parent.right
                    delegate: RowLayout {
                        property bool peerUp: c_status.init
                                              && c_status.peers[index].up
                        anchors.left: parent.left
                        anchors.right: parent.right
                        Text {
                            Layout.fillWidth: true
                            color: peerUp ? theme.palette.normal.foregroundText : theme.palette.normal.backgroundTertiaryText
                            text: peerName(c_status.peers[index].public_key,
                                           peers)
                        }
                        Row {

                            visible: peerUp
                            UITK.Icon {
                                source: '../../assets/arrow_down.png'
                                height: parent.height
                                keyColor: 'black'
                                color: 'blue'
                            }

                            Text {
                                text: toHuman(c_status.peers[index].rx)
                            }
                            UITK.Icon {
                                source: '../../assets/arrow_up.png'
                                height: parent.height
                                keyColor: 'black'
                                color: 'green'
                            }
                            Text {
                                text: toHuman(c_status.peers[index].tx)
                            }
                            Text {
                                text: ' - ' + ago(
                                          c_status.peers[index].latest_handshake)
                            }
                        }
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
            if(listmodel.count > 0)
                showStatus();
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
        if (delta > 86400) {
            return Math.round(delta / 86400) + 'd'
        }
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
        python.call('vpn.instance.list_profiles', [], function (profiles) {
            listmodel.clear()
            for (var i = 0; i < profiles.length; i++) {
                profiles[i].init = false
                listmodel.append(profiles[i])
            }
        })
    }
    function showStatus() {
        python.call('vpn.instance.interface.current_status_by_interface', [],
                    function (all_status) {
                        const keys = Object.keys(all_status)
                        for (var i = 0; i < listmodel.count; i++) {
                            const entry = listmodel.get(i)

                            let status = {
                                "init": false
                            }
                            for (const idx in Object.keys(all_status)) {
                                const key = keys[idx]
                                const i_status = all_status[key]
                                if (entry.interface_name === key) {
                                    status = i_status
                                    status['init'] = true
                                    break
                                }
                            }
                            listmodel.setProperty(i, 'c_status', status)
                        }
                    })
    }

    Python {
        id: python
        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl('../../src/'))
            importModule('vpn', function () {
                python.call('vpn.instance.set_pwd', [root.pwd], function(result){});
                populateProfiles();
                if(listmodel.count > 0)
                    showStatus();
            })
        }
    }
}
