import QtQuick 2.7
import QtQuick.Layouts 1.3
import Qt.labs.settings 1.0
import io.thp.pyotherside 1.3
import Lomiri.Components 1.3 as UITK
import Lomiri.Components.Popups 1.3

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
            text: i18n.tr("Your password is required to use the wireguard kernel modules.")

            signal accepted(string password)
            signal rejected()

            UITK.TextField {
                id: passwordTextField
                echoMode: TextInput.Password
            }
            UITK.Button {
                text: i18n.tr("OK")
                color: UITK.LomiriColors.green
                onClicked: {
                    python.call('test.test_sudo',
                                [passwordTextField.text],
                                function(result){
                                    if(result) {
                                        passwordDialog.accepted(passwordTextField.text)
                                        PopupUtils.close(passwordDialog)
                                    }
                                    else {
                                        console.log("Passwordcheck failed")
                                    }
                                });
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
        // check if user has set a sudo pwd and show password prompt if so:
        python.call('test.test_sudo',
                    [""], // check with empty password
                    function(result) {
                        if(!result) {
                            var popup = PopupUtils.open(passwordPopup)
                            popup.accepted.connect(function(password) {
                                root.pwd = password;
                                checkFinished();
                            });
                            popup.rejected.connect(function() {
                                console.log("canceled!");
                                Qt.quit();
                            });
                        } else {
                            checkFinished();
                        }
                    });

        function checkFinished()
        {
            if (settings.finishedWizard) {
                stack.push(Qt.resolvedUrl("pages/PickProfilePage.qml"));
            } else {
                stack.push(Qt.resolvedUrl("pages/WizardPage.qml"));
            }
        }
    }

    Python {
        id: python
        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl('../src/'))
            importModule('test', function () {})
        }
    }
}
