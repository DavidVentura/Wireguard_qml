import QtQuick 2.0
import QtQuick.Layouts 1.12
import Qt.labs.settings 1.0
import Ubuntu.Components 1.3 as UITK
import io.thp.pyotherside 1.3

import "../components"

UITK.Page {
    property bool isEditing: false
    property string errorMsg
    property string profileName
    property string peerKey
    property string allowedPrefixes
    property string ipAddress
    property string endpoint
    property string privateKey
    property string extraRoutes

    Settings {
        id: settings
    }
    header: UITK.PageHeader {
        id: header
        title: "Manage profile"
    }

    Flickable {
        id: flick
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: save.top
        anchors.topMargin: units.gu(2)
        contentHeight: col.height
        contentWidth: width

        Column {
            id: col
            anchors.fill: parent
            spacing: units.gu(1)
            SettingsItem {
                title: i18n.ctr("download icon setting", "Profile name")
                control: UITK.TextField {
                    text: profileName
                    enabled: !isEditing
                    onTextChanged: {
                        errorMsg = ''
                        profileName = text
                    }
                }
            }
            SettingsItem {
                title: i18n.ctr("download icon setting", "Peer's public key")
                control: UITK.TextField {
                    text: peerKey
                    onTextChanged: {
                        errorMsg = ''
                        peerKey = text
                    }
                    placeholderText: "c29tZSBzaWxseSBzdHVmZgo="
                }
            }
            SettingsItem {
                title: i18n.ctr("download icon setting", "Allowed IP prefixes")
                control: UITK.TextField {
                    onTextChanged: {
                        text: allowedPrefixes
                        errorMsg = ''
                        allowedPrefixes = text
                    }
                    placeholderText: "10.0.0.1/32, 192.168.1.0/24"
                }
            }
            SettingsItem {
                title: i18n.ctr("download icon setting",
                                "IP address with netmask")
                control: UITK.TextField {
                    text: ipAddress
                    onTextChanged: {
                        errorMsg = ''
                        ipAddress = text
                    }
                    placeholderText: "10.0.0.14/24"
                }
            }
            SettingsItem {
                title: i18n.ctr("download icon setting", "Endpoint with port")
                control: UITK.TextField {
                    text: endpoint
                    onTextChanged: {
                        errorMsg = ''
                        endpoint = text
                    }
                    placeholderText: "vpn.example.com:1234"
                }
            }
            SettingsItem {
                title: i18n.ctr("download icon setting", "Private Key")
                control: Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    RowLayout {
                        anchors.right: parent.right
                        anchors.left: parent.left
                        spacing: units.gu(1)
                        UITK.TextField {
                            id: privateKeyField
                            Layout.fillWidth: true
                            text: privateKey
                            onTextChanged: {
                                errorMsg = ''
                                privateKey = text
                            }
                            placeholderText: "a2VlcCB0aGlzIHNlY3JldAo="
                        }
                        UITK.Button {
                            id: genKey
                            text: "Generate"
                            onClicked: {
                                privateKeyField.text = python.call_sync(
                                            'vpn.genkey', [])
                            }
                        }
                        UITK.Button {
                            text: "Copy pubkey"
                            enabled: privateKey
                            onClicked: {
                                const pubkey = python.call_sync(
                                                 'vpn.genpubkey', [privateKey])
                                UITK.Clipboard.push(pubkey)
                                toast.show('Public key copied to clipboard')
                            }
                        }
                    }
                }
            }
            SettingsItem {
                title: i18n.ctr("download icon setting", "Extra routes")
                control: UITK.TextField {
                    text: extraRoutes
                    onTextChanged: {
                        extraRoutes = text
                        errorMsg = ''
                    }
                }
            }
            UITK.Label {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: units.gu(2)
                anchors.rightMargin: units.gu(2)
                wrapMode: Text.WordWrap
                visible: errorMsg
                text: errorMsg
                color: 'red'
            }
        }
    }

    UITK.Button {
        id: save
        text: "Save"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: units.gu(2)
        anchors.leftMargin: units.gu(2)
        anchors.rightMargin: units.gu(2)
        enabled: peerKey && profileName && allowedPrefixes && ipAddress
                 && endpoint && privateKey
        onClicked: {
            errorMsg = ''
            python.call('vpn.save_profile',
                        [profileName, peerKey, allowedPrefixes, ipAddress, endpoint, privateKey, extraRoutes],
                        function (error) {
                            console.log(error)
                            if (!error) {
                                stack.clear()
                                stack.push(Qt.resolvedUrl(
                                               "PickProfilePage.qml"))
                                return
                            }
                            errorMsg = error
                        })
        }
    }
    Python {
        id: python
        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl('../../src/'))
            importModule('vpn', function () {})
        }
    }
}
