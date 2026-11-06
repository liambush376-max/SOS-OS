// SOS Quick Stats: compact CPU / RAM / temperature readout for the panel.
// Data comes from /usr/bin/sos-quickstats (JSON on stdout) via the
// Plasma5Support "executable" engine, which ships with plasma-workspace.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property real cpu: 0
    property real ram: 0
    property var temp: null
    readonly property string command: "sos-quickstats"

    Plasmoid.icon: "sos-monitor"
    toolTipMainText: "SOS Quick Stats"
    toolTipSubText: "CPU " + cpu.toFixed(0) + "%  ·  RAM " + ram.toFixed(0) + "%"
        + (temp !== null ? "  ·  " + temp.toFixed(0) + " °C" : "")
        + "\nClick to open SOS System Monitor"

    P5Support.DataSource {
        id: stats
        engine: "executable"
        connectedSources: [root.command]
        interval: 2000
        onNewData: (sourceName, data) => {
            if (data["exit code"] !== 0) {
                return
            }
            try {
                const s = JSON.parse(data["stdout"])
                root.cpu = s.cpu
                root.ram = s.ram
                root.temp = (s.temp === null || s.temp === undefined) ? null : s.temp
            } catch (e) {
                console.warn("sos-quickstats: bad output", e)
            }
        }
    }

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        onNewData: (sourceName) => disconnectSource(sourceName)
        function exec(cmd) { connectSource(cmd) }
    }

    component Meter: ColumnLayout {
        property string label
        property real value
        property color barColor
        spacing: 1
        PlasmaComponents.Label {
            Layout.alignment: Qt.AlignHCenter
            text: label + " " + value.toFixed(0) + (label === "°" ? "" : "%")
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
        }
        Rectangle {
            Layout.preferredWidth: Kirigami.Units.gridUnit * 2.4
            Layout.preferredHeight: 3
            radius: 1.5
            color: Qt.rgba(1, 1, 1, 0.12)
            Rectangle {
                width: parent.width * Math.min(1, value / 100)
                height: parent.height
                radius: 1.5
                color: barColor
                Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
            }
        }
    }

    compactRepresentation: MouseArea {
        Layout.minimumWidth: row.implicitWidth + Kirigami.Units.smallSpacing * 2
        hoverEnabled: true
        onClicked: launcher.exec("sos-monitor")

        RowLayout {
            id: row
            anchors.centerIn: parent
            spacing: Kirigami.Units.smallSpacing * 2
            Meter { label: "CPU"; value: root.cpu; barColor: "#2F7BFF" }
            Meter { label: "RAM"; value: root.ram; barColor: "#9B3DFF" }
            Meter {
                visible: root.temp !== null
                label: "°"
                value: root.temp === null ? 0 : root.temp
                barColor: root.temp !== null && root.temp > 80 ? "#FF5470" : "#38D696"
            }
        }
    }

    fullRepresentation: compactRepresentation
    preferredRepresentation: compactRepresentation
}
