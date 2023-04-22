import QtQuick 2.0
import QtQuick.Layouts 1.0
import Lomiri.Components 1.3 as UITK

RowLayout {
    property alias title: t.text
    property alias description: d.text
    property alias control: loader.sourceComponent

    anchors.left: parent.left
    anchors.right: parent.right
    spacing: units.gu(2)
    Column {
        Layout.alignment: Qt.AlignVCenter
        spacing: units.gu(0.2)
        Layout.fillWidth: true
        UITK.Label {
            id: t
            anchors.left: parent.left
            anchors.right: parent.right
        }
        UITK.Label {
            id: d
            anchors.left: parent.left
            anchors.right: parent.right
            color: '#ccc' // FIXME
        }
    }
    Loader {
        width: units.gu(6)
        id: loader
    }
}
