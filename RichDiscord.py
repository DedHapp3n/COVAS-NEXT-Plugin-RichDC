from typing import override
from lib.PluginHelper import PluginHelper, PluginManifest
from lib.PluginSettingDefinitions import PluginSettings, SettingsGrid, ToggleSetting
from lib.PluginBase import PluginBase
import os, sys, time, traceback

PLUGIN_DIR = os.path.abspath(os.path.dirname(__file__))
DEPS_DIR   = os.path.join(PLUGIN_DIR, "deps")
DEBUG_LOG_FILE = os.path.join(PLUGIN_DIR, "Debug_Log.txt")

if os.path.isdir(DEPS_DIR) and DEPS_DIR not in sys.path:
    sys.path.insert(0, DEPS_DIR)

def as_bool(v, default=False):
    if isinstance(v, bool): return v
    if v is None: return default
    if isinstance(v, (int, float)): return v != 0
    if isinstance(v, str): return v.strip().lower() in ("1","true","yes","on","y","t")
    return default

def debug_log(always: bool, msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        print(f"[RichDiscord DEBUG] {msg}")

def _try_read_setting(helper: PluginHelper, plugin_key: str, grid_key: str, field_key: str):
    # Probiert mehrere mögliche API-Methoden aus
    candidates = [
        ("get_setting_value",    (plugin_key, grid_key, field_key)),
        ("get_plugin_setting",   (plugin_key, grid_key, field_key)),
        ("get_setting",          (plugin_key, grid_key, field_key)),
        ("get_value",            (plugin_key, grid_key, field_key)),
        ("get",                  (plugin_key, grid_key, field_key)),
    ]
    for name, args in candidates:
        fn = getattr(helper, name, None)
        if callable(fn):
            try:
                return fn(*args)
            except Exception as e:
                debug_log(True, f"[Settings] {name}{args} -> error: {e}")
    raise AttributeError("no known get_setting* method on PluginHelper")

class RichDiscord(PluginBase):
    def __init__(self, plugin_manifest: PluginManifest):
        super().__init__(plugin_manifest)
        self.rpc = None
        self.connected = False
        self.client_id = "1403441212119318741"
        self.start_time = int(time.time())
        self.helper: PluginHelper | None = None

        # Caches (werden via on_settings_changed aktuell gehalten)
        self.enabled_cached = False
        self.debug_cached = False

        self.settings_config: PluginSettings | None = PluginSettings(
            key="RichDiscordPlugin",
            label="Rich Presence for Discord",
            icon="waving_hand",
            grids=[SettingsGrid(
                key="general",
                label="General",
                fields=[
                    ToggleSetting(
                        key="enabled",
                        label="Discord Rich Presence aktivieren",
                        type="toggle",
                        readonly=False,
                        placeholder=None,
                        default_value=False
                    ),
                    ToggleSetting(
                        key="debug_enabled",
                        label="Debug-Log aktivieren",
                        type="toggle",
                        readonly=False,
                        placeholder=None,
                        default_value=False
                    ),
                ]
            )]
        )

    # --- intern ---
    def _debug_on(self) -> bool:
        return self.debug_cached

    def _connect(self) -> bool:
        if self.connected and self.rpc:
            debug_log(True, "[Discord] Verbindung besteht bereits")
            return True
        try:
            from pypresence import Presence
            debug_log(True, "[Discord] pypresence import OK")
            self.rpc = Presence(self.client_id)
            debug_log(True, "[Discord] Verbindungsaufbau wird versucht…")
            self.rpc.connect()
            self.connected = True
            debug_log(True, "[Discord] Verbindung erfolgreich aufgebaut")
            return True
        except Exception as e:
            debug_log(True, f"[Discord] Verbindung fehlgeschlagen: {e}\n{traceback.format_exc()}")
            self.rpc = None
            self.connected = False
            return False

    def _set_presence_min(self):
        if not self._connect():
            return
        try:
            try: self.rpc.clear()
            except Exception: pass
            self.rpc.update(details="COVAS", state="aktiv", start=self.start_time)
            debug_log(True, "[Discord] Presence gesetzt (minimal)")
        except Exception as e:
            debug_log(True, f"[Discord] Presence setzen fehlgeschlagen: {e}")

    def _clear_presence(self):
        try:
            if self.rpc:
                try: self.rpc.clear()
                except Exception: pass
                try: self.rpc.close()
                except Exception: pass
                debug_log(True, "[Discord] Verbindung geschlossen und Presence gelöscht")
        except Exception:
            pass
        self.rpc = None
        self.connected = False

    def _load_initial_settings(self):
        # Versuche echte Werte zu lesen; fallback auf Cache (Defaults)
        enabled = self.enabled_cached
        debug_enabled = self.debug_cached
        if self.helper:
            try:
                enabled = as_bool(_try_read_setting(self.helper, "RichDiscordPlugin", "general", "enabled"), enabled)
            except Exception as e:
                debug_log(True, f"[Settings] read enabled failed -> {e}")
            try:
                debug_enabled = as_bool(_try_read_setting(self.helper, "RichDiscordPlugin", "general", "debug_enabled"), debug_enabled)
            except Exception as e:
                debug_log(True, f"[Settings] read debug_enabled failed -> {e}")
        self.enabled_cached = enabled
        self.debug_cached = debug_enabled
        debug_log(True, f"[Settings] enabled={self.enabled_cached}, debug_enabled={self.debug_cached}")

    # --- Lifecycle ---
    @override
    def on_plugin_helper_ready(self, helper: PluginHelper):
        self.helper = helper
        debug_log(True, f"=== Plugin gestartet am {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        self._load_initial_settings()
        if self.enabled_cached:
            self._set_presence_min()
        else:
            debug_log(True, "[Discord] Verbindung nicht aktiv (Toggle aus)")
            self._clear_presence()

    @override
    def on_settings_changed(self, helper: PluginHelper, plugin_key: str, grid_key: str, field_key: str, value):
        if plugin_key != "RichDiscordPlugin" or grid_key != "general":
            return
        if field_key == "enabled":
            self.enabled_cached = as_bool(value, False)
            debug_log(True, f"[Settings] enabled -> {self.enabled_cached}")
            if self.enabled_cached:
                self._set_presence_min()
            else:
                self._clear_presence()
        elif field_key == "debug_enabled":
            self.debug_cached = as_bool(value, False)
            debug_log(True, f"[Settings] debug_enabled -> {self.debug_cached}")

    @override
    def on_chat_stop(self, helper: PluginHelper):
        debug_log(True, "[Lifecycle] Plugin wird gestoppt")
        self._clear_presence()
