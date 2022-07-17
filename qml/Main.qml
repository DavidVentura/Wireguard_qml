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
            text: i18n.tr(
                      "The wireguard binary needs to be setuid; your sudo password is needed for this")

            signal accepted(string password)
            signal rejected

            UITK.Label {
                id: error
                color: "red"
                text: ""
                font.pixelSize: units.gu(1.5)
                visible: text != ""
                wrapMode: Text.Wrap
            }

            UITK.TextField {
                id: passwordTextField
                echoMode: TextInput.Password
            }
            UITK.Button {
                text: i18n.tr("OK")
                color: UITK.UbuntuColors.green
                onClicked: {
                    python.call('test.setuid_daemon', [passwordTextField.text],
                                function (result) {
                                    if (result === true) {
                                        passwordDialog.accepted(
                                                    passwordTextField.text)
                                        PopupUtils.close(passwordDialog)
                                    } else {
                                        error.text = result
                                    }
                                })
                }
            }
            UITK.Button {
                text: i18n.tr("Cancel")
                onClicked: {
                    passwordDialog.rejected()
                    PopupUtils.close(passwordDialog)
                }
            }
        }
    }

    function checkFinished() {
        if (settings.finishedWizard) {
            stack.push(Qt.resolvedUrl("pages/PickProfilePage.qml"))
        } else {
            stack.push(Qt.resolvedUrl("pages/WizardPage.qml"))
        }
    }

    Python {
        id: python
        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl('../src/'))
            importModule('test', function () {
                if (python.call_sync("test.needs_sudo")) {
                    if (python.call_sync("test.setuid_daemon", [""]) === true) {
                        checkFinished()
                        return
                    }
                    var popup = PopupUtils.open(passwordPopup)
                    popup.accepted.connect(function (password) {
                        root.pwd = password
                        checkFinished()
                    })
                    popup.rejected.connect(function () {
                        console.log("canceled!")
                        Qt.quit()
                    })
                }
            })
        }
    }
}
