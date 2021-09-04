import Ubuntu.Components 1.3 as UITK
import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12

Item {
    property string title
    property alias text: tf.text
    property string placeholder: ''
    property alias enabled: tf.enabled
    property alias control: loader.sourceComponent
    signal changed(string text)

    anchors.left: parent.left
    anchors.right: parent.right
    anchors.leftMargin: units.gu(2)
    anchors.rightMargin: units.gu(2)

    //    anchors.verticalCenter: parent.verticalCenter
    height: childrenRect.height

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        TextField {
            id: tf
            Layout.fillWidth: true
            placeholderText: '<font color="#ccc">' + placeholder + '</font>'
            topPadding: units.gu(1)
            bottomPadding: units.gu(1)
            leftPadding: units.gu(1)
            background: Rectangle {
                radius: units.gu(0.8)
                color: tf.enabled ? "white" : "#eee"
                border.color: "#ccc" // fixme
                border.width: 1
            }
            onTextChanged: changed(text)
        }
        Loader {
            height: tf.height
            id: loader
        }
    }
    Label {
        id: lb
        x: tf.x + units.gu(1.5)
        y: tf.y - height / 2
        z: 2
        text: title
        color: '#333'
        font.pixelSize: units.gu(1.25)
    }

    Rectangle {
        color: tf.background.color
        x: lb.x - units.gu(0.5)
        y: tf.y //lb.y + lb.height / 2
        width: lb.width + units.gu(1)
        height: lb.height / 2
    }
}
