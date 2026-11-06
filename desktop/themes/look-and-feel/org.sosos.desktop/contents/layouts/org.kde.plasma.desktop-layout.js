// SOS OS default desktop layout (Plasma 6 desktop scripting API).
// Runs once, when a user logs in with no existing Plasma configuration.

var wallpaper = "file:///usr/share/wallpapers/SOS-Aurora/";

var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    var desk = desktopsArray[j];
    desk.wallpaperPlugin = "org.kde.image";
    desk.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desk.writeConfig("Image", wallpaper);
    desk.writeConfig("FillMode", "2");
}

// Floating, centred bottom dock-style panel. KWin's blur effect gives the
// translucent "frosted glass" look behind it.
var panel = new Panel();
panel.location = "bottom";
panel.height = 2 * Math.floor(gridUnit * 2.6 / 2);
panel.floating = true;
panel.alignment = "center";
panel.hiding = "none";

var launcher = panel.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["Shortcuts"];
launcher.writeConfig("global", "Alt+F1");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "start-here-sos");
launcher.writeConfig("showAppsByName", "true");
launcher.writeConfig("favorites", [
    "preferred://browser",
    "preferred://filemanager",
    "org.kde.konsole.desktop",
    "sos-settings.desktop",
    "sos-monitor.desktop",
    "sos-updater.desktop",
    "sos-devhub.desktop"
].join(","));

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "preferred://filemanager",
    "preferred://browser",
    "applications:org.kde.konsole.desktop",
    "applications:sos-settings.desktop"
].join(","));
tasks.writeConfig("indicateAudioStreams", "true");

panel.addWidget("org.kde.plasma.marginsseparator");
panel.addWidget("org.sosos.quickstats");
// System tray = notification centre + quick settings (network, audio,
// Bluetooth, battery, brightness, night light, do-not-disturb).
panel.addWidget("org.kde.plasma.systemtray");

var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", "true");
clock.writeConfig("dateFormat", "shortDate");

panel.addWidget("org.kde.plasma.showdesktop");
