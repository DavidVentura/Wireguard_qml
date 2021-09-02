import QtQuick 2.0
import Ubuntu.Components 1.3 as UITK

Row {
    property string title
    property alias control: loader.sourceComponent

    anchors.left: parent.left
    anchors.right: parent.right
    anchors.leftMargin: units.gu(2)
    anchors.rightMargin: units.gu(2)
    spacing: units.gu(2)

    Column {
        spacing: units.gu(0.2)
        width: parent.width
        anchors.verticalCenter: parent.verticalCenter
        UITK.Label {
            anchors.left: parent.left
            anchors.right: parent.right
            text: title
        }
        Loader {
            anchors.left: parent.left
            anchors.right: parent.right
            id: loader
        }
    }
}
