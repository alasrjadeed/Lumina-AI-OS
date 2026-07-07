import subprocess

from core.log import log


class AndroidDevice:
    def __init__(self):
        self._serial: str | None = None

    def _adb(self, *args: str) -> subprocess.CompletedProcess:
        cmd = ["adb"]
        if self._serial:
            cmd += ["-s", self._serial]
        cmd += list(args)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    def detect_devices(self) -> list[dict]:
        result = self._adb("devices")
        devices = []
        for line in result.stdout.strip().split("\n")[1:]:
            if line.strip() and "device" in line:
                serial = line.split("\t")[0]
                devices.append({"serial": serial, "status": "connected"})
        log.info("Detected %d Android device(s)", len(devices))
        return devices

    def connect(self, serial: str | None = None):
        if serial:
            self._serial = serial
        else:
            devices = self.detect_devices()
            if devices:
                self._serial = devices[0]["serial"]
        log.info("Connected to device: %s", self._serial or "none")

    def disconnect(self):
        self._serial = None

    @property
    def is_connected(self) -> bool:
        return self._serial is not None

    def shell(self, command: str) -> str:
        result = self._adb("shell", command)
        return result.stdout

    def install_apk(self, apk_path: str) -> dict:
        result = self._adb("install", "-r", apk_path)
        ok = "Success" in result.stdout
        log.info("Install APK %s: %s", apk_path, "OK" if ok else "FAILED")
        return {"success": ok, "output": result.stdout.strip()}

    def screenshot(self, path: str = "/sdcard/screen.png") -> str:
        self._adb("shell", "screencap", "-p", path)
        log.info("Screenshot saved: %s", path)
        return path

    def pull(self, remote: str, local: str):
        self._adb("pull", remote, local)

    def push(self, local: str, remote: str):
        self._adb("push", local, remote)

    def list_packages(self, filter_str: str = "") -> list[str]:
        cmd = "pm list packages"
        if filter_str:
            cmd += f" | grep {filter_str}"
        output = self.shell(cmd)
        return [p.replace("package:", "").strip() for p in output.strip().split("\n") if p.strip()]

    def get_logcat(self, lines: int = 50) -> str:
        result = self._adb("logcat", "-d", "-t", str(lines))
        return result.stdout

    def get_device_info(self) -> dict:
        return {
            "model": self.shell("getprop ro.product.model").strip(),
            "manufacturer": self.shell("getprop ro.product.manufacturer").strip(),
            "android_version": self.shell("getprop ro.build.version.release").strip(),
            "sdk": self.shell("getprop ro.build.version.sdk").strip(),
            "battery": self.shell("dumpsys battery | grep level").strip(),
        }

    def input_tap(self, x: int, y: int):
        self._adb("shell", "input", "tap", str(x), str(y))

    def input_text(self, text: str):
        self._adb("shell", "input", "text", text.replace(" ", "%s"))

    def input_keyevent(self, keycode: int):
        self._adb("shell", "input", "keyevent", str(keycode))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        self._adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))

    def press_back(self):
        self.input_keyevent(4)

    def press_home(self):
        self.input_keyevent(3)


android = AndroidDevice()
