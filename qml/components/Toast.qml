import QtQuick 2.0
import QtQuick.Controls 2.12

Popup {
    padding: units.dp(12)

    x: parent.width / 2 - width / 2
    y: parent.height - height - units.dp(20)

    background: Rectangle {
        color: "#111111"
        opacity: 0.85
        radius: units.dp(10)
    }

    Text {
        id: popupLabel
        anchors.fill: parent
        horizontalAlignment: Text.AlignHCenter
        color: "#ffffff"
        font.pixelSize: units.dp(14)
    }

    Timer {
        id: popupTimer
        interval: 2000
        running: true
        onTriggered: {
            toast.close()
        }
    }

    function show(text) {
        popupLabel.text = text
        open()
        popupTimer.restart()
    }
}
