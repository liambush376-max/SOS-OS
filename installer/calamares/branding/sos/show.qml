// Calamares installation slideshow for SOS OS (slideshowAPI 2).
import QtQuick
import calamares.slideshow 1.0

Presentation {
    id: presentation

    function onActivate() { advanceTimer.running = true }
    function onLeave() { advanceTimer.running = false }

    Timer {
        id: advanceTimer
        interval: 9000
        repeat: true
        running: false
        onTriggered: presentation.goToNextSlide()
    }

    component SosSlide: Slide {
        property string heading
        property string body
        Rectangle {
            anchors.fill: parent
            color: "#0E1024"
            Column {
                anchors.centerIn: parent
                width: parent.width * 0.75
                spacing: 18
                Text {
                    width: parent.width
                    text: heading
                    color: "#E6E9FF"
                    font.pixelSize: 28
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 120; height: 3; radius: 1.5
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: "#2F7BFF" }
                        GradientStop { position: 1; color: "#B04DFF" }
                    }
                }
                Text {
                    width: parent.width
                    text: body
                    color: "#8C92BA"
                    font.pixelSize: 16
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    SosSlide {
        heading: "Welcome to SOS OS"
        body: "A fast, dark and modern desktop built on Debian 13 and KDE Plasma 6."
    }
    SosSlide {
        heading: "Ready for games"
        body: "Open SOS Welcome after installing to add Steam, Proton, GameMode and MangoHud, and switch on Gaming Mode in the Control Center."
    }
    SosSlide {
        heading: "Ready for code"
        body: "The developer tool set adds Git, GCC, Clang, Python, Podman and the GitHub CLI, and SOS DevHub clones and opens your projects."
    }
    SosSlide {
        heading: "Secure by default"
        body: "Signed Debian updates, a firewall that's on out of the box, optional full-disk encryption, and no listening services."
    }
}
