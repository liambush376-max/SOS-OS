// SOS OS login screen for SDDM (Qt 6 greeter, Theme-API 2.0).
// Context objects provided by SDDM: sddm, userModel, sessionModel, config,
// keyboard, screenModel.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Qt5Compat.GraphicalEffects

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#05060F"

    readonly property color accent: config.accent || "#2F7BFF"
    readonly property color accent2: config.accentSecondary || "#9B3DFF"
    readonly property color fg: "#E6E9FF"
    readonly property color fgDim: "#8C92BA"
    property int sessionIndex: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0

    LayoutMirroring.enabled: Qt.locale().textDirection === Qt.RightToLeft
    LayoutMirroring.childrenInherit: true

    function doLogin() {
        errorText.text = ""
        busy.running = true
        sddm.login(userField.currentUser(), passwordField.text, root.sessionIndex)
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            busy.running = false
            passwordField.text = ""
            passwordField.forceActiveFocus()
            errorText.text = "Incorrect password. Try again."
            shake.start()
        }
        function onLoginSucceeded() {
            busy.running = false
        }
    }

    Image {
        id: bg
        anchors.fill: parent
        source: config.background || "background.png"
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
    }

    // Clock
    Column {
        anchors.top: parent.top
        anchors.topMargin: parent.height * 0.1
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 4
        Text {
            id: clock
            anchors.horizontalCenter: parent.horizontalCenter
            color: root.fg
            font.pixelSize: 96
            font.weight: Font.Light
            text: Qt.formatTime(new Date(), "hh:mm")
        }
        Text {
            id: date
            anchors.horizontalCenter: parent.horizontalCenter
            color: root.fgDim
            font.pixelSize: 22
            text: Qt.formatDate(new Date(), "dddd, d MMMM")
        }
        Timer {
            interval: 10000; running: true; repeat: true
            onTriggered: {
                clock.text = Qt.formatTime(new Date(), "hh:mm")
                date.text = Qt.formatDate(new Date(), "dddd, d MMMM")
            }
        }
    }

    // Frosted-glass login card
    Item {
        id: card
        width: 420
        height: 360
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 80

        ShaderEffectSource {
            id: behind
            sourceItem: bg
            sourceRect: Qt.rect(card.x, card.y, card.width, card.height)
            visible: false
        }
        FastBlur {
            anchors.fill: parent
            source: behind
            radius: 64
            layer.enabled: true
            layer.effect: OpacityMask {
                maskSource: Rectangle { width: card.width; height: card.height; radius: 24 }
            }
        }
        Rectangle {
            anchors.fill: parent
            radius: 24
            color: Qt.rgba(0.07, 0.08, 0.17, 0.55)
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.12)
        }
        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            height: 3
            radius: 1.5
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: root.accent }
                GradientStop { position: 1; color: root.accent2 }
            }
        }

        SequentialAnimation {
            id: shake
            NumberAnimation { target: card; property: "anchors.horizontalCenterOffset"; to: -14; duration: 50 }
            NumberAnimation { target: card; property: "anchors.horizontalCenterOffset"; to: 14; duration: 80 }
            NumberAnimation { target: card; property: "anchors.horizontalCenterOffset"; to: -8; duration: 70 }
            NumberAnimation { target: card; property: "anchors.horizontalCenterOffset"; to: 0; duration: 50 }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 36
            anchors.topMargin: 40
            spacing: 14

            Image {
                Layout.alignment: Qt.AlignHCenter
                source: "logo.png"
                sourceSize.width: 72
                sourceSize.height: 72
            }

            ComboBox {
                id: userField
                Layout.fillWidth: true
                model: userModel
                textRole: "name"
                currentIndex: {
                    for (let i = 0; i < userModel.count; i++) {
                        if (userModel.data(userModel.index(i, 0), Qt.UserRole + 1) === userModel.lastUser)
                            return i
                    }
                    return 0
                }
                editable: userModel.count === 0
                function currentUser() { return editable ? editText : currentText }
                font.pixelSize: 16
                contentItem: Text {
                    leftPadding: 14
                    text: userField.displayText
                    color: root.fg
                    font: userField.font
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitHeight: 44
                    radius: 12
                    color: Qt.rgba(1, 1, 1, 0.07)
                    border.color: userField.activeFocus ? root.accent : Qt.rgba(1, 1, 1, 0.12)
                }
            }

            TextField {
                id: passwordField
                Layout.fillWidth: true
                echoMode: TextInput.Password
                placeholderText: "Password"
                placeholderTextColor: root.fgDim
                color: root.fg
                font.pixelSize: 16
                focus: true
                leftPadding: 14
                background: Rectangle {
                    implicitHeight: 44
                    radius: 12
                    color: Qt.rgba(1, 1, 1, 0.07)
                    border.color: passwordField.activeFocus ? root.accent : Qt.rgba(1, 1, 1, 0.12)
                }
                Keys.onReturnPressed: root.doLogin()
                Keys.onEnterPressed: root.doLogin()
            }

            Button {
                id: loginButton
                Layout.fillWidth: true
                text: busy.running ? "Signing in…" : "Sign in"
                enabled: !busy.running
                onClicked: root.doLogin()
                contentItem: Text {
                    text: loginButton.text
                    color: "white"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitHeight: 44
                    radius: 12
                    opacity: loginButton.down ? 0.8 : 1
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: root.accent }
                        GradientStop { position: 1; color: root.accent2 }
                    }
                }
                BusyIndicator {
                    id: busy
                    running: false
                    visible: running
                    anchors.right: parent.right
                    anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    width: 24; height: 24
                }
            }

            Text {
                id: errorText
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                color: "#FF5470"
                font.pixelSize: 13
                text: keyboard.capsLock ? "Caps Lock is on" : ""
            }
        }
    }

    // Bottom bar: session picker + power actions
    RowLayout {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 28
        spacing: 12

        ComboBox {
            id: sessionBox
            model: sessionModel
            textRole: "name"
            currentIndex: root.sessionIndex
            onActivated: root.sessionIndex = currentIndex
            implicitWidth: 240
            contentItem: Text {
                leftPadding: 12
                text: "Session: " + sessionBox.displayText
                color: root.fg
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle { implicitHeight: 36; radius: 10; color: Qt.rgba(1, 1, 1, 0.08) }
        }

        Item { Layout.fillWidth: true }

        Repeater {
            model: [
                { label: "Suspend", act: "suspend", show: sddm.canSuspend },
                { label: "Restart", act: "reboot", show: sddm.canReboot },
                { label: "Shut down", act: "poweroff", show: sddm.canPowerOff }
            ]
            delegate: Button {
                required property var modelData
                visible: modelData.show
                text: modelData.label
                onClicked: {
                    if (modelData.act === "suspend") sddm.suspend()
                    else if (modelData.act === "reboot") sddm.reboot()
                    else sddm.powerOff()
                }
                contentItem: Text { text: parent.text; color: root.fg; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { implicitHeight: 36; implicitWidth: 110; radius: 10; color: parent.hovered ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(1, 1, 1, 0.08) }
            }
        }
    }

    Component.onCompleted: passwordField.forceActiveFocus()
}
