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
    def __init__(self):
        super().__init__()

        # Compute bounding rect across ALL screens
        combined = QRect()
        for screen in QApplication.screens():
            combined = combined.united(screen.geometry())

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.BypassWindowManagerHint  # Prevents slide-in animation on macOS
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Explicit geometry instead of showFullScreen() — fixes macOS black screen
        self.setGeometry(combined)

        self.start_point = None
        self.end_point = None
        self.is_selecting = False
        self.loading_popup = None
        self.analysis_thread = None
        self.analysis_worker = None

        self.show()
        self.activateWindow()
        self.raise_()
        self.setFocus()

    def _disable_window_animation_macos(self):
        """Kill the slide-in animation via native AppKit call."""
        if sys.platform == 'darwin':
            try:
                import objc
                from AppKit import NSApplication, NSWindowAnimationBehaviorNone
                ns_app = NSApplication.sharedApplication()
                for win in ns_app.windows():
                    if win.isVisible():
                        win.setAnimationBehavior_(NSWindowAnimationBehaviorNone)
            except Exception as e:
                print(f"objc animation disable failed: {e}")

    def paintEvent(self, event):
        painter = QPainter(self)

        # Dark overlay across full screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if self.is_selecting and self.start_point and self.end_point:
            selection_rect = QRect(self.start_point, self.end_point).normalized()

            # Punch a transparent hole — CompositionMode_Source works on macOS Metal
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(selection_rect, QColor(0, 0, 0, 0))

            # Cyan border around selection
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
        if sys.platform == 'darwin':
            self._disable_window_animation_macos()

    def capture_and_analyze(self, x, y, w, h):
        try:
            self.hide()
            QApplication.processEvents()

            if sys.platform == 'darwin':
                import time
                time.sleep(0.15)

            # Use a proper writable path instead of relative "captured_claim.png"
            if sys.platform == 'darwin':
                import tempfile
                save_path = os.path.join(tempfile.gettempdir(), "captured_claim.png")
            elif sys.platform == 'win32':
                save_path = os.path.join(os.environ.get('TEMP', os.getcwd()), "captured_claim.png")
            else:
                save_path = os.path.join(os.path.expanduser("~"), "captured_claim.png")

            # Find which screen contains the selection
            target_screen = QApplication.primaryScreen()
            for screen in QApplication.screens():
                if screen.geometry().contains(x, y):
                    target_screen = screen
                    break

            screen_geo = target_screen.geometry()
            local_x = x - screen_geo.x()
            local_y = y - screen_geo.y()
            pixmap = target_screen.grabWindow(0, local_x, local_y, w, h)
            pixmap.save(save_path, "PNG")

            print(f"📸 Screenshot saved to: {save_path}")
            print("🧠 RealityLens is verifying...")

            self.loading_popup = LoadingPopup()
            self.loading_popup.show()
            QApplication.processEvents()

            self.analysis_thread = QThread()
            self.analysis_worker = AnalyzerWorker(save_path)
            self.analysis_worker.moveToThread(self.analysis_thread)

            self.analysis_thread.started.connect(self.analysis_worker.run)
            self.analysis_worker.status_changed.connect(self._update_loading_status)
            self.analysis_worker.finished.connect(self.on_analysis_finished)
            self.analysis_worker.finished.connect(self.analysis_thread.quit)
            self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
            self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)

            self.analysis_thread.start()

        except Exception as e:
            print(f"❌ Error: {e}")

    def on_analysis_finished(self, verdict_text):
        if self.loading_popup:
            self.loading_popup.close()
            self.loading_popup = None

        self.result_window = ResultPopup(verdict_text)
        self.result_window.show()

    def _update_loading_status(self, message):
        if self.loading_popup:
            self.loading_popup.set_status_text(message)


def main():
    if sys.platform == 'win32':
        ctypes.windll.shcore.SetProcessDpiAwareness(2)

    # Must be set BEFORE QApplication is created on macOS
    if sys.platform == 'darwin':
        try:
            from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
            NSApplication.sharedApplication().setActivationPolicy_(
                NSApplicationActivationPolicyAccessory
            )
        except Exception as e:
            print(f"Failed to set accessory policy: {e}")

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

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

    def on_hotkey():
        hotkey_handler.trigger.emit()

    from pynput import keyboard

    def start_hotkey_listener():
        hotkeys = {
            '<ctrl>+<shift>+l': on_hotkey,
            '<cmd>+<shift>+l': on_hotkey
        }
        with keyboard.GlobalHotKeys(hotkeys) as listener:
            listener.join()

    active_overlays = []

    def launch_ui():
        def create_overlay():
            # Bring app to front before showing overlay — fixes .app bundle hotkey issue
            if sys.platform == 'darwin':
                try:
                    from AppKit import NSApplication
                    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
                except Exception as e:
                    print(f"Failed to activate app: {e}")

            overlay = SnippingOverlay()
            active_overlays.append(overlay)
            overlay.destroyed.connect(lambda: active_overlays.remove(overlay))

        QTimer.singleShot(0, create_overlay)

    hotkey_handler.trigger.connect(launch_ui)

    hotkey_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
    hotkey_thread.start()

    if sys.platform == "win32":
        power_filter = WindowsPowerEventFilter(start_hotkey_listener)
        app.installNativeEventFilter(power_filter)

    print("RealityLens is active. Press Ctrl+Shift+L (Win/Linux) or Cmd+Shift+L (Mac) to verify.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()