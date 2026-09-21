# DNS Switcher für Windows

Eine kleine Python-GUI zum schnellen Wechseln der DNS-Server eines Windows-Netzwerkadapters.

## Voraussetzungen

- Windows 10 oder Windows 11
- Python 3.10 oder neuer (inklusive Tkinter; bei python.org standardmäßig enthalten)

## Start

`DNS-Switcher-starten.bat` doppelt anklicken. Alternativ:

```powershell
python dns_switcher.py
```

Windows zeigt eine Administrator-Abfrage an, da DNS-Einstellungen nur mit erhöhten Rechten geändert werden können.

## Enthaltene Profile

- Automatisch (DHCP)
- Cloudflare
- Google
- Quad9 (gefiltert)
- AdGuard DNS
- Benutzerdefinierte IPv4- und/oder IPv6-Adressen

Für manuelle Einträge stehen vier Felder zur Verfügung: bevorzugtes und alternatives IPv4 sowie bevorzugtes und alternatives IPv6. IPv4 und IPv6 können gemeinsam eingetragen und angewendet werden. Beim Tippen in eines der Felder wird das benutzerdefinierte Profil automatisch ausgewählt.

## Eigene Profile speichern

1. Die gewünschten IPv4- und IPv6-DNS-Server eintragen.
2. Unter **Profilname** einen Namen vergeben.
3. **Speichern** anklicken.

Das Profil erscheint anschließend in der Profilauswahl und bleibt auch nach einem Neustart erhalten. Zum Entfernen das eigene Profil auswählen und **Löschen** anklicken. Gespeichert wird unter `%APPDATA%\DNS-Switcher\profiles.json`.

## Standard und vorherige Einstellung

- **Standard (DHCP)** setzt den gewählten Adapter sofort auf die automatische DNS-Zuweisung von Windows zurück.
- **Vorherige Einstellung** stellt die vor dem letzten Wechsel verwendeten DNS-Adressen wieder her. Die letzte Einstellung wird pro Netzwerkadapter gespeichert und bleibt nach einem Neustart des Tools erhalten.

Nach jeder Änderung leert das Programm automatisch den lokalen DNS-Cache.
