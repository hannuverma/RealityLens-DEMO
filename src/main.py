import os
import sys
import threading
from PyQt6.QtCore import QTimer
if sys.platform == "win32" and getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    possible_bin_paths = [
        os.path.join(base_path, 'PyQt6', 'Qt6', 'bin'),
        os.path.join(base_path, '_internal', 'PyQt6', 'Qt6', 'bin'),
        os.path.join(base_path, 'PyQt6', 'plugins', 'platforms'),
    ]
    for bin_path in possible_bin_paths:
        if os.path.exists(bin_path):
            os.add_dll_directory(bin_path)

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget, QMessageBox
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QObject, QThread
import pyautogui
from ui.components import ResultPopup, LoadingPopup, AnalyzerWorker

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from PyQt6.QtCore import QAbstractNativeEventFilter
import ctypes

if sys.platform == "win32":
    import ctypes.wintypes


if sys.platform == "win32":
    class WindowsPowerEventFilter(QAbstractNativeEventFilter):
        def __init__(self, restart_callback):
            super().__init__()
            self.restart_callback = restart_callback

        def nativeEventFilter(self, eventType, message):
            if eventType == "windows_generic_MSG":
                msg = ctypes.wintypes.MSG.from_address(int(message))
                WM_POWERBROADCAST = 0x0218
                PBT_APMRESUMEAUTOMATIC = 0x0012
                PBT_APMRESUMESUSPEND = 0x0007
                if msg.message == WM_POWERBROADCAST:
                    if msg.wParam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                        print("🔋 System resumed from sleep — restarting hotkeys")
                        self.restart_callback()
            return False, 0


def check_mac_permissions():
    """
    Runs the accessibility check on macOS and shows a dialog if permissions
    are missing. Called after QApplication is created so the dialog renders.
    """
    import subprocess
    result = subprocess.run(
        ['osascript', '-e', 'tell application "System Events" to get name of first process'],
        capture_output=True
    )
    if result.returncode != 0:
        msg = QMessageBox()
        msg.setWindowTitle("Permissions Required")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "RealityLens needs Accessibility & Screen Recording permissions.\n\n"
            "Please go to:\n"
            "System Settings → Privacy & Security → Accessibility\n"
            "and add this app, then restart."
        )
        msg.exec()


class HotkeySignal(QObject):
    trigger = pyqtSignal()


class SnippingOverlay(QWidget):
    analysis_in_progress = False

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.showFullScreen()
        self.activateWindow()
        self.raise_()
        self.setFocus()

        self.start_point = None
        self.end_point = None
        self.is_selecting = False
        self.loading_popup = None
        self.analysis_thread = None
        self.analysis_worker = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self.is_selecting and self.start_point and self.end_point:
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(0, 255, 255), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        self.start_point = event.globalPosition().toPoint()
        self.end_point = self.start_point
        self.is_selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False
        selection_rect = QRect(self.start_point, self.end_point).normalized()
        x, y, w, h = selection_rect.getRect()
        print(f"✅ Real Screen Coordinates: X={x}, Y={y}, W={w}, H={h}")

        if w > 5 and h > 5:
            self.capture_and_analyze(x, y, w, h)

        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.is_selecting = False
            self.close()
            return
        super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.setFocus()

    def capture_and_analyze(self, x, y, w, h):
        try:
            if SnippingOverlay.analysis_in_progress:
                return

            SnippingOverlay.analysis_in_progress = True
            self.hide()
            QApplication.processEvents()

            screenshot = pyautogui.screenshot(region=(int(x), int(y), int(w), int(h)))
            save_path = "captured_claim.png"
            screenshot.save(save_path)

            print("🧠 RealityLens is verifying...")
            self.loading_popup = LoadingPopup()
            self.loading_popup.show()
            QApplication.processEvents()

            self.analysis_thread = QThread()
            self.analysis_worker = AnalyzerWorker(save_path)
            self.analysis_worker.moveToThread(self.analysis_thread)

            self.analysis_thread.started.connect(self.analysis_worker.run)
            self.analysis_worker.finished.connect(self.on_analysis_finished)
            self.analysis_worker.finished.connect(self.analysis_thread.quit)
            self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
            self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)

            self.analysis_thread.start()

        except Exception as e:
            SnippingOverlay.analysis_in_progress = False
            print(f"❌ Error: {e}")

    def on_analysis_finished(self, verdict_text):
        SnippingOverlay.analysis_in_progress = False
        if self.loading_popup:
            self.loading_popup.close()
            self.loading_popup = None

        self.result_window = ResultPopup(verdict_text)
        self.result_window.show()


def main():
    if sys.platform == 'win32':
        ctypes.windll.shcore.SetProcessDpiAwareness(2)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Mac permission check — runs here so QApplication exists for the dialog
    if sys.platform == 'darwin':
        check_mac_permissions()

    # System tray
    tray = QSystemTrayIcon(app)
    tray.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon))
    menu = QMenu()
    exit_action = menu.addAction("Exit RealityLens")
    exit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.show()

    hotkey_handler = HotkeySignal()
    
    # Holds the ONE active overlay. Cleared when it closes so no memory leak.

    def on_hotkey():
        hotkey_handler.trigger.emit()

    pressed_keys = set()

    from pynput import keyboard

    def start_hotkey_listener():
        hotkeys = {
            '<ctrl>+<shift>+l': on_hotkey,   # Windows / Linux
            '<cmd>+<shift>+l': on_hotkey     # macOS
        }

        with keyboard.GlobalHotKeys(hotkeys) as listener:
            listener.join()


    active_overlays = []

    def launch_ui():
        if SnippingOverlay.analysis_in_progress:
            return

        def create_overlay():
            overlay = SnippingOverlay()
            active_overlays.append(overlay)
            overlay.destroyed.connect(lambda: active_overlays.remove(overlay))
            overlay.show()

        QTimer.singleShot(0, create_overlay)

    hotkey_handler.trigger.connect(launch_ui)

    hotkey_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
    hotkey_thread.start()

    if sys.platform == "win32":
        power_filter = WindowsPowerEventFilter(start_hotkey_listener)
        app.installNativeEventFilter(power_filter)

    print("RealityLens is active. Press Ctrl+Shift+L to verify.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()