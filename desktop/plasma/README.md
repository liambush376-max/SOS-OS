# Plasma integration map

Where each part of the SOS OS desktop experience lives:

| Feature | Implementation | Source |
| --- | --- | --- |
| Global theme ("SOS OS") | Plasma look-and-feel package `org.sosos.desktop` | `../themes/look-and-feel/` |
| Colour scheme | `SOSDark.colors` | `../themes/color-schemes/` |
| Taskbar / panel | Floating, centred bottom panel from the layout script | `../themes/look-and-feel/org.sosos.desktop/contents/layouts/` |
| Application launcher | Kickoff with SOS icon and favourites | layout script |
| Frosted-glass panels | KWin blur + contrast effects on Plasma's translucent panel | `../configuration/rootfs/etc/xdg/kwinrc` |
| Smooth animations | KWin effects (scale, magic lamp, slide, overview), duration factor | `kwinrc`, `kdeglobals` |
| Notification centre, quick settings | Plasma system tray (notifications, network, audio, Bluetooth, battery, night light) | layout script |
| Panel widget | SOS Quick Stats plasmoid | `../widgets/org.sosos.quickstats/` |
| Login splash | KSplash QML | `../themes/look-and-feel/org.sosos.desktop/contents/splash/` |
| Login screen | SDDM theme `sos` | `../sddm/sos/` |
| Boot splash | Plymouth theme `sos` | `../plymouth/sos/` |
| Boot menu (installed) | GRUB theme | `../grub/sos/` |
| File manager styling | Dolphin follows the colour scheme and Breeze Dark icons | `kdeglobals` |
| Window decorations | Breeze with SOS shadows/colours | `../configuration/rootfs/etc/xdg/breezerc` |

System-wide defaults sit in `/etc/xdg`, so users can still override everything
in their own `~/.config`.
