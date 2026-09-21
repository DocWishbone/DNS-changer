"""Kleine Windows-GUI zum schnellen Wechseln der DNS-Server."""

from __future__ import annotations

import ctypes
import ipaddress
import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


APP_TITLE = "DNS Switcher"
CREATE_NO_WINDOW = 0x08000000
PROFILE_FILE = Path(os.environ.get("APPDATA", str(Path.home()))) / "DNS-Switcher" / "profiles.json"
STATE_FILE = PROFILE_FILE.with_name("state.json")

DNS_PROFILES = {
    "Automatisch (DHCP)": None,
    "Cloudflare": ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"],
    "Google": ["8.8.8.8", "8.8.4.4", "2001:4860:4860::8888", "2001:4860:4860::8844"],
    "Quad9 (gefiltert)": ["9.9.9.9", "149.112.112.112", "2620:fe::fe", "2620:fe::9"],
    "AdGuard DNS": ["94.140.14.14", "94.140.15.15", "2a10:50c0::ad1:ff", "2a10:50c0::ad2:ff"],
    "Benutzerdefiniert": "custom",
}


def powershell(script: str, *, check: bool = True) -> str:
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=CREATE_NO_WINDOW,
    )
    if check and completed.returncode:
        error = completed.stderr.strip() or completed.stdout.strip() or "Unbekannter PowerShell-Fehler"
        raise RuntimeError(error)
    return completed.stdout.strip()


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def restart_as_admin() -> None:
    script = str(Path(__file__).resolve())
    parameters = subprocess.list2cmdline([script, *sys.argv[1:]])
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, parameters, None, 1)
    if result <= 32:
        raise RuntimeError("Die Administrator-Anfrage konnte nicht gestartet werden.")


def get_adapters() -> list[str]:
    command = (
        "@(Get-NetAdapter | Where-Object { $_.Status -ne 'Disabled' } | "
        "Sort-Object @{Expression={$_.Status -eq 'Up'};Descending=$true}, Name | "
        "Select-Object -ExpandProperty Name) | ConvertTo-Json -Compress"
    )
    raw = powershell(command)
    if not raw:
        return []
    result = json.loads(raw)
    return [result] if isinstance(result, str) else result


def get_dns(adapter: str) -> list[str]:
    command = (
        f"@(Get-DnsClientServerAddress -InterfaceAlias {ps_quote(adapter)} "
        "-ErrorAction Stop | ForEach-Object ServerAddresses) | ConvertTo-Json -Compress"
    )
    raw = powershell(command)
    if not raw:
        return []
    result = json.loads(raw)
    return [result] if isinstance(result, str) else result


class DnsSwitcher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("680x700")
        self.minsize(620, 660)
        self.option_add("*Font", ("Segoe UI", 10))

        self.custom_profiles = self.load_profiles()
        self.adapter_state = self.load_state()
        self.updating_fields = False
        self.adapter_var = tk.StringVar()
        self.profile_var = tk.StringVar(value="Cloudflare")
        self.profile_name_var = tk.StringVar()
        self.ipv4_primary_var = tk.StringVar()
        self.ipv4_secondary_var = tk.StringVar()
        self.ipv6_primary_var = tk.StringVar()
        self.ipv6_secondary_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Bereit")
        self.current_var = tk.StringVar(value="–")

        self._build_ui()
        self.profile_var.trace_add("write", self._profile_changed)
        self.adapter_var.trace_add("write", lambda *_: self.refresh_status())
        for variable in self.dns_field_vars:
            variable.trace_add("write", self._custom_edited)
        self._toggle_custom()
        self.refresh_adapters()

    @staticmethod
    def load_profiles() -> dict[str, list[str]]:
        try:
            if not PROFILE_FILE.exists():
                return {}
            data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
            valid: dict[str, list[str]] = {}
            for name, servers in data.items():
                if isinstance(name, str) and isinstance(servers, list) and 1 <= len(servers) <= 4:
                    checked = [str(ipaddress.ip_address(server)) for server in servers]
                    valid[name] = checked
            return valid
        except (OSError, ValueError, TypeError, AttributeError, json.JSONDecodeError):
            return {}

    def persist_profiles(self) -> None:
        PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROFILE_FILE.write_text(
            json.dumps(self.custom_profiles, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def load_state() -> dict[str, dict[str, list[str] | None]]:
        try:
            if not STATE_FILE.exists():
                return {}
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return {}

    def persist_state(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(self.adapter_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update_profile_list(self) -> None:
        self.profile_box["values"] = [*DNS_PROFILES, *sorted(self.custom_profiles, key=str.casefold)]

    @property
    def dns_field_vars(self) -> tuple[tk.StringVar, ...]:
        return (
            self.ipv4_primary_var,
            self.ipv4_secondary_var,
            self.ipv6_primary_var,
            self.ipv6_secondary_var,
        )

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)

        ttk.Label(outer, text="DNS-Server wechseln", font=("Segoe UI Semibold", 17)).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 18)
        )

        ttk.Label(outer, text="Netzwerkadapter").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=6)
        self.adapter_box = ttk.Combobox(outer, textvariable=self.adapter_var, state="readonly")
        self.adapter_box.grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(outer, text="Aktualisieren", command=self.refresh_adapters).grid(row=1, column=2, padx=(10, 0), pady=6)

        ttk.Label(outer, text="DNS-Profil").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=6)
        self.profile_box = ttk.Combobox(
            outer,
            textvariable=self.profile_var,
            values=[*DNS_PROFILES, *sorted(self.custom_profiles, key=str.casefold)],
            state="readonly",
        )
        self.profile_box.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(outer, text="IPv4 bevorzugt").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=6)
        self.ipv4_primary_entry = ttk.Entry(outer, textvariable=self.ipv4_primary_var)
        self.ipv4_primary_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(outer, text="IPv4 alternativ").grid(row=4, column=0, sticky="w", padx=(0, 12), pady=6)
        self.ipv4_secondary_entry = ttk.Entry(outer, textvariable=self.ipv4_secondary_var)
        self.ipv4_secondary_entry.grid(row=4, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(outer, text="IPv6 bevorzugt").grid(row=5, column=0, sticky="w", padx=(0, 12), pady=6)
        self.ipv6_primary_entry = ttk.Entry(outer, textvariable=self.ipv6_primary_var)
        self.ipv6_primary_entry.grid(row=5, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(outer, text="IPv6 alternativ").grid(row=6, column=0, sticky="w", padx=(0, 12), pady=6)
        self.ipv6_secondary_entry = ttk.Entry(outer, textvariable=self.ipv6_secondary_var)
        self.ipv6_secondary_entry.grid(row=6, column=1, columnspan=2, sticky="ew", pady=6)
        ttk.Label(
            outer,
            text="IPv4 und IPv6 können gemeinsam in einem Profil gespeichert werden.",
            foreground="#666666",
        ).grid(row=7, column=1, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(outer, text="Profilname").grid(row=8, column=0, sticky="w", padx=(0, 12), pady=6)
        ttk.Entry(outer, textvariable=self.profile_name_var).grid(row=8, column=1, sticky="ew", pady=6)
        profile_buttons = ttk.Frame(outer)
        profile_buttons.grid(row=8, column=2, sticky="e", padx=(10, 0), pady=6)
        ttk.Button(profile_buttons, text="Speichern", command=self.save_profile).pack(side="left", padx=(0, 5))
        ttk.Button(profile_buttons, text="Löschen", command=self.delete_profile).pack(side="left")

        ttk.Separator(outer).grid(row=9, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(outer, text="Aktuell").grid(row=10, column=0, sticky="nw", padx=(0, 12), pady=8)
        ttk.Label(outer, textvariable=self.current_var, wraplength=410).grid(
            row=10, column=1, columnspan=2, sticky="w", pady=8
        )

        button_row = ttk.Frame(outer)
        button_row.grid(row=11, column=0, columnspan=3, sticky="ew", pady=(18, 8))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)
        ttk.Button(button_row, text="DNS anwenden", command=self.apply_dns).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(button_row, text="DNS-Cache leeren", command=self.flush_dns).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(button_row, text="Standard (DHCP)", command=self.apply_default).grid(
            row=1, column=0, sticky="ew", padx=(0, 6), pady=(10, 0)
        )
        ttk.Button(button_row, text="Vorherige Einstellung", command=self.restore_previous).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=(10, 0)
        )

        ttk.Label(outer, textvariable=self.status_var, foreground="#245c8a").grid(
            row=12, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )

    def _toggle_custom(self) -> None:
        # Die Felder bleiben bearbeitbar; Eingaben aktivieren automatisch das manuelle Profil.
        for entry in (
            self.ipv4_primary_entry,
            self.ipv4_secondary_entry,
            self.ipv6_primary_entry,
            self.ipv6_secondary_entry,
        ):
            entry.configure(state="normal")

    def _profile_changed(self, *_: object) -> None:
        self._toggle_custom()
        name = self.profile_var.get()
        if name not in self.custom_profiles:
            return
        servers = self.custom_profiles[name]
        ipv4 = [server for server in servers if ipaddress.ip_address(server).version == 4]
        ipv6 = [server for server in servers if ipaddress.ip_address(server).version == 6]
        self.updating_fields = True
        try:
            self.ipv4_primary_var.set(ipv4[0] if ipv4 else "")
            self.ipv4_secondary_var.set(ipv4[1] if len(ipv4) > 1 else "")
            self.ipv6_primary_var.set(ipv6[0] if ipv6 else "")
            self.ipv6_secondary_var.set(ipv6[1] if len(ipv6) > 1 else "")
            self.profile_name_var.set(name)
        finally:
            self.updating_fields = False

    def _custom_edited(self, *_: object) -> None:
        if self.updating_fields:
            return
        if any(variable.get().strip() for variable in self.dns_field_vars) and self.profile_var.get() != "Benutzerdefiniert":
            self.profile_var.set("Benutzerdefiniert")

    def manual_servers(self) -> list[str]:
        values = [variable.get().strip() for variable in self.dns_field_vars if variable.get().strip()]
        if not values:
            raise ValueError("Bitte mindestens eine eigene DNS-Adresse eingeben.")
        parsed = [ipaddress.ip_address(value) for value in values]
        field_versions = (4, 4, 6, 6)
        filled = [(index, value) for index, value in enumerate(self.dns_field_vars) if value.get().strip()]
        for (index, _), address in zip(filled, parsed):
            if address.version != field_versions[index]:
                raise ValueError(f"Die Adresse „{address}“ steht im falschen IPv{field_versions[index]}-Feld.")
        return [str(address) for address in parsed]

    def save_profile(self) -> None:
        name = self.profile_name_var.get().strip()
        if not name:
            messagebox.showwarning(APP_TITLE, "Bitte einen Namen für das Profil eingeben.")
            return
        if name in DNS_PROFILES:
            messagebox.showwarning(APP_TITLE, "Dieser Name ist für ein eingebautes Profil reserviert.")
            return
        try:
            servers = self.manual_servers()
            if name in self.custom_profiles and not messagebox.askyesno(APP_TITLE, f"Profil „{name}“ überschreiben?"):
                return
            self.custom_profiles[name] = servers
            self.persist_profiles()
            self.update_profile_list()
            self.profile_var.set(name)
            self.status_var.set(f"Profil „{name}“ wurde gespeichert.")
        except (ValueError, OSError) as exc:
            messagebox.showerror(APP_TITLE, f"Profil konnte nicht gespeichert werden:\n\n{exc}")

    def delete_profile(self) -> None:
        name = self.profile_var.get()
        if name not in self.custom_profiles:
            messagebox.showwarning(APP_TITLE, "Bitte zuerst ein selbst gespeichertes Profil auswählen.")
            return
        if not messagebox.askyesno(APP_TITLE, f"Profil „{name}“ wirklich löschen?"):
            return
        try:
            del self.custom_profiles[name]
            self.persist_profiles()
            self.update_profile_list()
            self.profile_var.set("Benutzerdefiniert")
            self.profile_name_var.set("")
            self.status_var.set(f"Profil „{name}“ wurde gelöscht.")
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Profil konnte nicht gelöscht werden:\n\n{exc}")

    def refresh_adapters(self) -> None:
        try:
            adapters = get_adapters()
            previous = self.adapter_var.get()
            self.adapter_box["values"] = adapters
            if previous in adapters:
                self.adapter_var.set(previous)
            elif adapters:
                self.adapter_var.set(adapters[0])
            else:
                self.adapter_var.set("")
                self.current_var.set("Keine aktiven Netzwerkadapter gefunden.")
            self.status_var.set("Adapterliste aktualisiert.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Adapter konnten nicht geladen werden:\n\n{exc}")

    def refresh_status(self) -> None:
        adapter = self.adapter_var.get()
        if not adapter:
            return
        try:
            addresses = get_dns(adapter)
            self.current_var.set(", ".join(addresses) if addresses else "Automatisch / keine Adresse gemeldet")
        except Exception as exc:
            self.current_var.set(f"Status nicht verfügbar: {exc}")

    def selected_servers(self) -> list[str] | None:
        profile_name = self.profile_var.get()
        if profile_name in self.custom_profiles:
            return self.custom_profiles[profile_name]
        selected = DNS_PROFILES[profile_name]
        if selected == "custom":
            return self.manual_servers()
        return selected

    def apply_dns(self) -> None:
        adapter = self.adapter_var.get()
        if not adapter:
            messagebox.showwarning(APP_TITLE, "Bitte einen Netzwerkadapter auswählen.")
            return
        try:
            servers = self.selected_servers()
            self.apply_setting(adapter, servers)
            self.status_var.set(f"Profil „{self.profile_var.get()}“ wurde auf „{adapter}“ angewendet.")
            messagebox.showinfo(APP_TITLE, "DNS-Einstellung wurde erfolgreich geändert.")
        except ValueError as exc:
            messagebox.showwarning(APP_TITLE, str(exc))
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"DNS konnte nicht geändert werden:\n\n{exc}")

    def apply_setting(self, adapter: str, servers: list[str] | None) -> None:
        old_setting = self.adapter_state.get(adapter, {}).get("current", get_dns(adapter))
        if servers is None:
            command = f"Set-DnsClientServerAddress -InterfaceAlias {ps_quote(adapter)} -ResetServerAddresses -ErrorAction Stop"
        else:
            quoted = ",".join(ps_quote(server) for server in servers)
            command = f"Set-DnsClientServerAddress -InterfaceAlias {ps_quote(adapter)} -ServerAddresses @({quoted}) -ErrorAction Stop"
        powershell(command)
        self.adapter_state[adapter] = {"current": servers, "previous": old_setting}
        self.persist_state()
        powershell("Clear-DnsClientCache", check=False)
        self.refresh_status()

    def apply_default(self) -> None:
        adapter = self.adapter_var.get()
        if not adapter:
            messagebox.showwarning(APP_TITLE, "Bitte einen Netzwerkadapter auswählen.")
            return
        try:
            self.apply_setting(adapter, None)
            self.profile_var.set("Automatisch (DHCP)")
            self.status_var.set(f"„{adapter}“ verwendet wieder die automatische DNS-Einstellung (DHCP).")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Standardeinstellung konnte nicht aktiviert werden:\n\n{exc}")

    def restore_previous(self) -> None:
        adapter = self.adapter_var.get()
        if not adapter:
            messagebox.showwarning(APP_TITLE, "Bitte einen Netzwerkadapter auswählen.")
            return
        state = self.adapter_state.get(adapter, {})
        if "previous" not in state:
            messagebox.showinfo(APP_TITLE, "Für diesen Adapter ist noch keine vorherige Einstellung gespeichert.")
            return
        try:
            previous = state["previous"]
            self.apply_setting(adapter, previous)
            self.status_var.set(f"Die vorherige DNS-Einstellung für „{adapter}“ wurde wiederhergestellt.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Vorherige Einstellung konnte nicht wiederhergestellt werden:\n\n{exc}")

    def flush_dns(self) -> None:
        try:
            powershell("Clear-DnsClientCache -ErrorAction Stop")
            self.status_var.set("DNS-Cache wurde geleert.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"DNS-Cache konnte nicht geleert werden:\n\n{exc}")


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("Dieses Programm ist für Windows vorgesehen.")
    if not is_admin():
        try:
            restart_as_admin()
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))
        return
    DnsSwitcher().mainloop()


if __name__ == "__main__":
    main()
