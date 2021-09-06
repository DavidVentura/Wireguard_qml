import QtQuick 2.7
import QtQuick.Layouts 1.3
import Qt.labs.settings 1.0
import io.thp.pyotherside 1.3
import Ubuntu.Components 1.3 as UITK

import "./pages"
import "./components"

UITK.MainView {
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

    Component.onCompleted: {
        if (settings.finishedWizard) {
            stack.push(Qt.resolvedUrl("pages/PickProfilePage.qml"))
        } else {
            stack.push(Qt.resolvedUrl("pages/WizardPage.qml"))
        }
    }
}
