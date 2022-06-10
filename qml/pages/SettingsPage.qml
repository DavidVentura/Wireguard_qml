import QtQuick 2.0
import Ubuntu.Components 1.3 as UITK
import io.thp.pyotherside 1.3
import Qt.labs.settings 1.0

import "../components"

UITK.Page {
    Settings {
        id: settings
        property bool finishedWizard: false
        property bool useUserspace: true
        property bool canUseKmod: false
    }
    header: UITK.PageHeader {
        id: header
        title: i18n.tr("Settings")

        leadingActionBar.actions: [
            UITK.Action {
                iconName: "back"
                onTriggered: {
                    // In case of useUserspace property changed,
                    // make sure PickProfilePage gets loaded new, so the settings object gets also refreshed
                    stack.clear()
                    stack.push(Qt.resolvedUrl("PickProfilePage.qml"))
                }
            }
        ]
    }
    ListView {
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: units.gu(2)
        anchors.leftMargin: units.gu(2)
        anchors.rightMargin: units.gu(2)
        Column {
            spacing: units.gu(1)
            anchors.left: parent.left
            anchors.right: parent.right
            SettingsItem {
                title: i18n.tr("Use slow userspace implementation")
                description: i18n.tr("It will be buggy, slow and probably crash.")
                control: UITK.Switch {
                    enabled: settings.canUseKmod
                    checked: settings.useUserspace
                    onCheckedChanged: settings.useUserspace = checked
                }
            }
            UITK.Button {
                text: i18n.tr("Try validating the kernel module again")
                anchors.left: parent.left
                anchors.right: parent.right
                onClicked: {
                    stack.clear()
                    stack.push(Qt.resolvedUrl("WizardPage.qml"))
                }
            }
        }
    }
}
