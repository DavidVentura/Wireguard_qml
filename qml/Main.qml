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

    width: units.gu(45)
    height: units.gu(75)

    //        Python {
    //            id: python
    //            Component.onCompleted: {
    //                addImportPath(Qt.resolvedUrl('../src/'))
    //                importModule('vpn', function () {
    //                    console.log("who")
    //                })
    //            }
    //        }
    Toast {
        id: toast
    }
    UITK.PageStack {
        anchors.fill: parent
        id: stack
    }

    Component.onCompleted: stack.push(Qt.resolvedUrl(
                                          "pages/PickProfilePage.qml"))
}
