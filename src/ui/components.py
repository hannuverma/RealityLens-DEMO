import os
import re
from pathlib import Path
import sys
import sys

from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
	QApplication,
	QHBoxLayout,
	QLabel,
	QProgressBar,
	QPushButton,
	QSlider,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
	

from ai_client import verify_content


STYLE_PATH = Path(resource_path(os.path.join("src", "ui", "style.qss")))
	

def _load_popup_style(accent_color: str) -> str:
	try:
		style_text = STYLE_PATH.read_text(encoding="utf-8")
	except OSError:
		style_text = ""
	return style_text.replace("__ACCENT__", accent_color)


def extract_confidence_score(text: str) -> int:
	match = re.search(r"confidence\s*score\s*[:\-]?\s*([0-9]{1,3})", text, re.IGNORECASE)
	if not match:
		match = re.search(r"\b([0-9]{1,3})\s*/\s*100\b", text)
	if not match:
		return 50
	value = int(match.group(1))
	return max(0, min(100, value))


def extract_verdict_label(text: str) -> str:
	lowered = text.lower()
	if "likely fake" in lowered or "fake" in lowered:
		return "Likely Fake"
	if "suspicious" in lowered:
		return "Suspicious"
	if "likely real" in lowered or "real" in lowered:
		return "Likely Real"
	return "Analysis Complete"


def verdict_color(text: str) -> str:
	lowered = text.lower()
	if "fake" in lowered:
		return "#FF4B4B"
	if "suspicious" in lowered:
		return "#FFD700"
	if "real" in lowered:
		return "#00FF7F"
	return "#00FFFF"


class AnalyzerWorker(QObject):
	finished = pyqtSignal(str)

	def __init__(self, image_path: str):
		super().__init__()
		self.image_path = image_path

	def run(self):
		result = verify_content(self.image_path)
		self.finished.emit(result)


class AnchoredPopup(QWidget):
	def move_to_bottom_right(self, margin: int = 20):
		screen = QApplication.primaryScreen()
		if not screen:
			return
		area = screen.availableGeometry()
		self.move(area.right() - self.width() - margin, area.bottom() - self.height() - margin)


class LoadingPopup(AnchoredPopup):
	def __init__(self):
		super().__init__()
		self.dot_step = 0
		self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
		self.setFixedSize(320, 120)
		self.setStyleSheet(_load_popup_style("#4ECDC4"))

		layout = QVBoxLayout(self)
		layout.setContentsMargins(10, 10, 10, 10)

		root = QWidget(self)
		root.setObjectName("LoadingRoot")
		root_layout = QVBoxLayout(root)
		root_layout.setContentsMargins(14, 14, 14, 14)
		root_layout.setSpacing(8)

		self.title = QLabel("RealityLens is verifying")
		self.title.setObjectName("LoadingTitle")
		root_layout.addWidget(self.title)

		hint = QLabel("Please wait while we analyze the capture...")
		hint.setObjectName("LoadingHint")
		root_layout.addWidget(hint)

		progress = QProgressBar()
		progress.setObjectName("LoadingBar")
		progress.setRange(0, 0)
		progress.setTextVisible(False)
		root_layout.addWidget(progress)

		layout.addWidget(root)

		self.timer = QTimer(self)
		self.timer.timeout.connect(self._tick)
		self.timer.start(350)

		self.move_to_bottom_right()

	def _tick(self):
		self.dot_step = (self.dot_step + 1) % 4
		self.title.setText(f"RealityLens is verifying{'.' * self.dot_step}")


class ResultPopup(AnchoredPopup):
	def __init__(self, text: str):
		super().__init__()
		self.result_text = text
		self.border_color = verdict_color(text)
		confidence = extract_confidence_score(text)
		verdict = extract_verdict_label(text)

		self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
		self.setWindowTitle("RealityLens Verdict")
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

		self.setMinimumSize(380, 240)
		self.resize(520, 360)
		self.setStyleSheet(_load_popup_style(self.border_color))

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(10, 10, 10, 10)

		root = QWidget(self)
		root.setObjectName("PopupRoot")
		content_layout = QVBoxLayout(root)
		content_layout.setContentsMargins(14, 14, 14, 14)
		content_layout.setSpacing(10)

		title = QLabel("RealityLens Verdict")
		title.setObjectName("TitleLabel")
		content_layout.addWidget(title)

		subtitle = QLabel(f"{verdict} • Confidence {confidence}%")
		subtitle.setObjectName("SubLabel")
		content_layout.addWidget(subtitle)

		slider_row = QHBoxLayout()
		confidence_label = QLabel("Confidence")
		confidence_label.setObjectName("SubLabel")
		slider_row.addWidget(confidence_label)

		confidence_slider = QSlider(Qt.Orientation.Horizontal)
		confidence_slider.setObjectName("ConfidenceSlider")
		confidence_slider.setRange(0, 100)
		confidence_slider.setValue(confidence)
		confidence_slider.setEnabled(False)
		slider_row.addWidget(confidence_slider, 1)

		score_label = QLabel(f"{confidence}%")
		score_label.setObjectName("SubLabel")
		slider_row.addWidget(score_label)
		content_layout.addLayout(slider_row)

		meter = QProgressBar()
		meter.setObjectName("TrustMeter")
		meter.setRange(0, 100)
		meter.setValue(confidence)
		meter.setFormat(f"Trust Meter: {confidence}%")
		content_layout.addWidget(meter)

		body = QTextEdit()
		body.setObjectName("BodyEdit")
		body.setReadOnly(True)
		body.setPlainText(text)
		content_layout.addWidget(body, 1)

		actions_layout = QHBoxLayout()
		copy_btn = QPushButton("Copy")
		copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.result_text))
		actions_layout.addWidget(copy_btn)

		dismiss_btn = QPushButton("Dismiss")
		dismiss_btn.setObjectName("PrimaryButton")
		dismiss_btn.clicked.connect(self.close)
		actions_layout.addWidget(dismiss_btn)
		content_layout.addLayout(actions_layout)

		main_layout.addWidget(root)
		self.move_to_bottom_right()
