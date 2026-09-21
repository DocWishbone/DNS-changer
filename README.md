# DNS Switcher for Windows

[Deutsch](#deutsch) · [English](#english)

---

## Deutsch

### DNS Switcher für Windows

Eine kleine Python-GUI zum schnellen Wechseln der DNS-Server eines Windows-Netzwerkadapters.

### Voraussetzungen

- Windows 10 oder Windows 11
- Python 3.10 oder neuer (inklusive Tkinter; bei python.org standardmäßig enthalten)

### Start

`DNS-Switcher-starten.bat` doppelt anklicken. Alternativ:

```powershell
python dns_switcher.py
```

Windows zeigt eine Administrator-Abfrage an, da DNS-Einstellungen nur mit erhöhten Rechten geändert werden können.

### Enthaltene Profile

- Automatisch (DHCP)
- Cloudflare
- Google
- Quad9 (gefiltert)
- AdGuard DNS
- Benutzerdefinierte IPv4- und/oder IPv6-Adressen

Für manuelle Einträge stehen vier Felder zur Verfügung: bevorzugtes und alternatives IPv4 sowie bevorzugtes und alternatives IPv6. IPv4 und IPv6 können gemeinsam eingetragen und angewendet werden. Beim Tippen in eines der Felder wird das benutzerdefinierte Profil automatisch ausgewählt.

### Eigene Profile speichern

1. Die gewünschten IPv4- und IPv6-DNS-Server eintragen.
2. Unter **Profilname** einen Namen vergeben.
3. **Speichern** anklicken.

Das Profil erscheint anschließend in der Profilauswahl und bleibt auch nach einem Neustart erhalten. Zum Entfernen das eigene Profil auswählen und **Löschen** anklicken. Gespeichert wird unter `%APPDATA%\DNS-Switcher\profiles.json`.

### Gespeichertes Profil laden

1. Die Liste **DNS-Profil** öffnen.
2. Das gewünschte gespeicherte Profil auswählen.
3. Den Netzwerkadapter auswählen.
4. **DNS anwenden** anklicken.

Die gespeicherten IPv4- und IPv6-Adressen werden beim Auswählen automatisch in die entsprechenden Felder geladen.

### Standard und vorherige Einstellung

- **Standard (DHCP)** setzt den gewählten Adapter sofort auf die automatische DNS-Zuweisung von Windows zurück.
- **Vorherige Einstellung** stellt die vor dem letzten Wechsel verwendeten DNS-Adressen wieder her. Die letzte Einstellung wird pro Netzwerkadapter gespeichert und bleibt nach einem Neustart des Tools erhalten.

Nach jeder Änderung leert das Programm automatisch den lokalen DNS-Cache.

---

## English

### DNS Switcher for Windows

A small Python GUI for quickly changing the DNS servers of a Windows network adapter.

### Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer, including Tkinter (included by default with Python from python.org)

### Starting the application

Double-click `DNS-Switcher-starten.bat`. Alternatively, run:

```powershell
python dns_switcher.py
```

Windows displays an administrator prompt because changing DNS settings requires elevated privileges.

### Included profiles

- Automatic (DHCP)
- Cloudflare
- Google
- Quad9 (filtered)
- AdGuard DNS
- Custom IPv4 and IPv6 addresses

Four fields are available for manual configuration: preferred and alternate IPv4, plus preferred and alternate IPv6. IPv4 and IPv6 addresses can be entered, saved, and applied together. Editing any of these fields automatically selects the custom profile.

### Saving custom profiles

1. Enter the desired IPv4 and IPv6 DNS servers.
2. Enter a name under **Profilname** (profile name).
3. Click **Speichern** (save).

The profile then appears in the profile list and remains available after restarting the application. To remove it, select the custom profile and click **Löschen** (delete). Profiles are stored in `%APPDATA%\DNS-Switcher\profiles.json`.

### Loading a saved profile

1. Open the **DNS-Profil** list.
2. Select the saved profile.
3. Select the network adapter.
4. Click **DNS anwenden** (apply DNS).

The saved IPv4 and IPv6 addresses are loaded into the corresponding fields automatically.

### Default and previous settings

- **Standard (DHCP)** immediately restores automatic Windows DNS assignment for the selected adapter.
- **Vorherige Einstellung** (previous setting) restores the DNS addresses used before the last change. The previous setting is stored separately for each network adapter and remains available after restarting the application.

The application automatically clears the local DNS cache after every change.
