import QtQuick 2.0
import Ubuntu.Components 1.3 as UITK
import io.thp.pyotherside 1.3

import "../components"

UITK.Page {
    property bool connected: true // FIXME
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
                iconName: "close"
                visible: connected
                onTriggered: {
                    python.call('vpn.interface.disconnect', [], function () {
                        toast.show("Disconnected")
                    })
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
        }

        delegate: UITK.ListItem {

            trailingActions: UITK.ListItemActions {
                actions: [
                    UITK.Action {
                        iconName: 'edit'
                        onTriggered: {
                            stack.push(Qt.resolvedUrl("ProfilePage.qml"), {
                                           "isEditing": true,
                                           "profileName": profile_name,
                                           "peerKey": peer_key,
                                           "allowedPrefixes": allowed_prefixes,
                                           "ipAddress": ip_address,
                                           "endpoint": endpoint,
                                           "privateKey": private_key,
                                           "extraRoutes": extra_routes
                                       })
                        }
                    },
                    UITK.Action {
                        iconName: 'webbrowser-app'
                        onTriggered: {
                            python.call('vpn._connect', [profile_name],
                                        function (error_msg) {
                                            if (error_msg) {
                                                toast.show('Failed:' + error_msg)
                                                return
                                            }
                                            toast.show('Connected')
                                        })
                        }
                    }
                ]
            }
            Column {
                anchors.leftMargin: units.gu(2)
                anchors.rightMargin: units.gu(2)
                anchors.topMargin: units.gu(2)
                anchors.bottomMargin: units.gu(2)
                anchors.fill: parent

                Text {
                    text: profile_name
                }
                Text {
                    text: endpoint
                }
            }
        }
    }

    UITK.Label {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        wrapMode: Text.WordWrap
        id: status_label
    }

    Timer {
        repeat: true
        interval: 1000
        running: true
        onTriggered: {
            showStatus()
        }
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
                    function (status) {
                        status_label.text = JSON.stringify(status, null, 2)
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
