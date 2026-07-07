"""Android device management — ADB-based automation and control.

Provides device connection, app lifecycle management, notification
monitoring, remote control via TCP, and voice interface integration.
"""

from core.android.client import AndroidClient, AppInfo, ScreenInfo
from core.android.device import AndroidDevice, android
from core.android.keyboard import Key, KeyPressResult, LuminaADBKeyboard
from core.android.notifications import AndroidNotification, AndroidNotificationManager
from core.android.remote_control import CommandResult, CommandType, RemoteCommand, RemoteControl
from core.android.voice import AndroidVoiceInterface, VoiceCaptureResult

__all__ = [
    "AndroidDevice",
    "android",
    "AndroidClient",
    "AppInfo",
    "ScreenInfo",
    "AndroidNotificationManager",
    "AndroidNotification",
    "RemoteControl",
    "RemoteCommand",
    "CommandType",
    "CommandResult",
    "AndroidVoiceInterface",
    "VoiceCaptureResult",
    "LuminaADBKeyboard",
    "KeyPressResult",
    "Key",
]
