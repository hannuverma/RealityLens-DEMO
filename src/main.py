import os
import sys



def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# This must run BEFORE from PyQt6 import ...
if getattr(sys, 'frozen', False):
    # sys._MEIPASS is the temporary folder where the EXE extracts itself
    base_path = sys._MEIPASS
    # This path must match exactly where you found the DLLs earlier
    qt_bin_path = os.path.join(base_path, '_internal', 'PyQt6', 'Qt6', 'bin')
    
    if os.path.exists(qt_bin_path):
        os.add_dll_directory(qt_bin_path)
    else:
        # Fallback for different PyInstaller versions
        alt_path = os.path.join(base_path, 'PyQt6', 'Qt6', 'bin')
        if os.path.exists(alt_path):
            os.add_dll_directory(alt_path)

import keyboard
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QObject, QThread, QTimer
import pyautogui
from ui.components import ResultPopup, LoadingPopup, AnalyzerWorker

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"



class HotkeySignal(QObject):
    trigger = pyqtSignal()

        
class SnippingOverlay(QWidget):
    analysis_in_progress = False

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
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
        # Draw a semi-transparent black overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if self.is_selecting and self.start_point and self.end_point:
            # "Cut out" the selection area (make it clear)
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.GlobalColor.transparent)
            
            # Draw a border around the selection
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(0, 255, 255), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        # globalPosition() gives absolute screen coordinates
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
        
        # These are the numbers we send to the Screen Capturer
        x, y, w, h = selection_rect.getRect()
        print(f"✅ Real Screen Coordinates: X={x}, Y={y}, W={w}, H={h}")
        
        # Check if selection is actually a box (prevent accidental clicks)
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
    # This MUST be the first thing that happens
    if sys.platform == 'win32':
        import ctypes
        # Use 2 for Per-Monitor DPI Awareness (Avoids the 'Access Denied' error)
        ctypes.windll.shcore.SetProcessDpiAwareness(2) 

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    # Keep the app alive in the tray even when all windows are closed.
    app.setQuitOnLastWindowClosed(False)


    # 2. Setup System Tray
    tray = QSystemTrayIcon(app)
    # Note: You'll need a 'logo.png' in your folder or use a standard icon
    tray.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon))
    
    menu = QMenu()
    exit_action = menu.addAction("Exit RealityLens")
    exit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.show()

    # 3. Setup Hotkey Listener
    hotkey_handler = HotkeySignal()
    overlay_container = [] # Keep reference to prevent garbage collection

    def on_hotkey():
        hotkey_handler.trigger.emit()

    def launch_ui():
        if SnippingOverlay.analysis_in_progress:
            print("RealityLens is still processing the previous selection. Please wait.")
            return

        new_overlay = SnippingOverlay()
        overlay_container.append(new_overlay)
        new_overlay.show()

    hotkey_handler.trigger.connect(launch_ui)
    keyboard.add_hotkey('ctrl+shift+l', on_hotkey)

    print("RealityLens is active. Press Ctrl+Shift+L to verify.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()