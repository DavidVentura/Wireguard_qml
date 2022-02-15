import QtQuick 2.7
import QtQuick.Layouts 1.3
import Qt.labs.settings 1.0
import io.thp.pyotherside 1.3
import Ubuntu.Components 1.3 as UITK
import Ubuntu.Components.Popups 1.3

import "./pages"
import "./components"

UITK.MainView {
    property string pwd

    id: root
    objectName: 'mainView'
    applicationName: 'wireguard.davidv.dev'
    automaticOrientation: true
    anchorToKeyboard: true

    width: units.gu(45)
    height: units.gu(75)

    Settings {
        id: settings
        property bool finishedWizard: false
    }

    Toast {
        id: toast
    }
    UITK.PageStack {
        anchors.fill: parent
        id: stack
    }

    Component {
        id: passwordPopup
        Dialog {
            id: passwordDialog
            title: i18n.tr("Enter password")
            text: i18n.tr("Your password is required for this action:")

            signal accepted(string password)
            signal rejected()

            UITK.TextField {
                id: passwordTextField
                echoMode: TextInput.Password
            }
            UITK.Button {
                text: i18n.tr("OK")
                color: UITK.UbuntuColors.green
                onClicked: {
                    passwordDialog.accepted(passwordTextField.text)
                    PopupUtils.close(passwordDialog)
                }
            }
            UITK.Button {
                text: i18n.tr("Cancel")
                onClicked: {
                    passwordDialog.rejected();
                    PopupUtils.close(passwordDialog)
                }
            }
        }
    }

    Component.onCompleted: {
        var popup = PopupUtils.open(passwordPopup)
        popup.accepted.connect(function(password) {
            root.pwd = password;

            if (settings.finishedWizard) {
                stack.push(Qt.resolvedUrl("pages/PickProfilePage.qml"))
            } else {
                stack.push(Qt.resolvedUrl("pages/WizardPage.qml"))
            }
        })
        popup.rejected.connect(function() {
            console.log("canceled!");
        })
    }
}
