// SOS OS login splash (KSplashQML). ksplash sets `stage` from 1 to 6.
import QtQuick

Rectangle {
    id: root
    color: "#05060F"

    property int stage

    onStageChanged: {
        if (stage === 2) {
            introAnimation.running = true
        }
    }

    Image {
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/SOS-Aurora/contents/images/1920x1080.png"
        fillMode: Image.PreserveAspectCrop
        opacity: 0.35
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        Image {
            id: logo
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -40
            source: "images/logo.png"
            sourceSize.width: 160
            sourceSize.height: 160

            SequentialAnimation on scale {
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 1.06; duration: 900; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.06; to: 1.0; duration: 900; easing.type: Easing.InOutSine }
            }
        }

        Text {
            anchors.top: logo.bottom
            anchors.topMargin: 28
            anchors.horizontalCenter: parent.horizontalCenter
            text: "SOS OS"
            color: "#E6E9FF"
            font.pixelSize: 30
            font.weight: Font.Light
            font.letterSpacing: 8
        }

        // Progress bar driven by ksplash stages
        Rectangle {
            id: track
            width: 260
            height: 4
            radius: 2
            color: "#1C1F3A"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: parent.height / 6

            Rectangle {
                height: parent.height
                radius: 2
                width: parent.width * Math.min(1, root.stage / 6)
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#2F7BFF" }
                    GradientStop { position: 1.0; color: "#B04DFF" }
                }
                Behavior on width { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }
            }
        }
    }

    OpacityAnimator {
        id: introAnimation
        running: false
        target: content
        from: 0
        to: 1
        duration: 600
        easing.type: Easing.InOutQuad
    }
}
