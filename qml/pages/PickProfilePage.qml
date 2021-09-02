import QtQuick 2.0
import Qt.labs.settings 1.0
import Ubuntu.Components 1.3 as UITK
import io.thp.pyotherside 1.3

import "../components"

UITK.Page {
    property bool loadedKp: false
    property bool pickingDB
    property bool busy

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
                    stack.push(Qt.resolvedUrl("CreateProfilePage.qml"))
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
                            stack.push(Qt.resolvedUrl("CreateProfilePage.qml"),
                                       {
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
    Python {
        id: python
        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl('../../src/'))
            importModule('vpn', function () {
                python.call('vpn.list_profiles', [], function (profiles) {
                    listmodel.clear()
                    for (var i = 0; i < profiles.length; i++) {
                        console.log(JSON.stringify(profiles[i], null, 2))
                        listmodel.append(profiles[i])
                    }
                })
            })
        }
    }
}
