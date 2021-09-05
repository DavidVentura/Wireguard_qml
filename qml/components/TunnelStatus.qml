import QtQuick 2.12
import QtQuick.Shapes 1.12
import QtGraphicalEffects 1.0

Shape {
    property bool connected
    property double size
    layer.enabled: true
    layer.samples: 6
    antialiasing: true
    height: units.gu(size + .1)
    width: units.gu(size + .1)
    id: spin
    ShapePath {
        id: shape
        fillColor: connected ? "#13C265" : "white"
        strokeColor: connected ? "#13C265" : "#ccc"
        strokeWidth: units.gu(0.1)
        capStyle: ShapePath.FlatCap

        PathAngleArc {
            id: arc
            centerX: spin.width / 2
            centerY: spin.height / 2
            radiusX: units.gu(size / 2)
            radiusY: units.gu(size / 2)
            startAngle: 0
            sweepAngle: 360
        }
    }
}
