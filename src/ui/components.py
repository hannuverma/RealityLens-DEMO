import os
import re
from pathlib import Path
import sys

from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
	QApplication,
	QHBoxLayout,
	QLabel,
	QProgressBar,
	QPushButton,
	QTextBrowser,
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

import json

def try_parse_json(data):
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)
    except Exception:
        return None


def _as_text(value: object) -> str:
	if value is None:
		return ""
	if isinstance(value, (dict, list)):
		return json.dumps(value, ensure_ascii=False, indent=2)
	return str(value)


STYLE_PATH = Path(resource_path(os.path.join("src", "ui", "style.qss")))
	

def _load_popup_style(accent_color: str) -> str:
	try:
		style_text = STYLE_PATH.read_text(encoding="utf-8")
	except OSError:
		style_text = ""
	return style_text.replace("__ACCENT__", accent_color)


def _to_percent(raw: object) -> int | None:
	try:
		value = float(raw)
	except (TypeError, ValueError):
		return None
	if value <= 1:
		value *= 100
	return max(0, min(100, int(round(value))))


def extract_scores(text: str) -> tuple[int, int]:
	data = try_parse_json(text)
	reality_score = None
	confidence_score = None

	if data:
		reality_score = _to_percent(data.get("reality_score"))
		confidence_score = _to_percent(data.get("confidence"))

	if reality_score is None and isinstance(text, str):
		match = re.search(r"reality\s*score\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
		if match:
			reality_score = _to_percent(match.group(1))

	if confidence_score is None and isinstance(text, str):
		match = re.search(r"confidence\s*score\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
		if match:
			confidence_score = _to_percent(match.group(1))

	if reality_score is None:
		reality_score = confidence_score if confidence_score is not None else 50

	if confidence_score is None:
		confidence_score = reality_score

	return reality_score, confidence_score


def extract_verdict_label(text: object) -> str:
	data = try_parse_json(text)

	if data and "verdict" in data:
		return str(data["verdict"])

	if not isinstance(text, str):
		return "Analysis Complete"

	lowered = text.lower()

	if "likely fake" in lowered:
		return "Likely Fake"

	if "suspicious" in lowered:
		return "Suspicious"

	if "likely real" in lowered:
		return "Likely Real"

	return "Analysis Complete"


def verdict_from_score(score: int) -> str:
	if score > 75:
		return "Likely Real"
	if score >= 40:
		return "Suspicious"
	return "Likely Fake"


def verdict_color(text: str) -> str:
	lowered = text.lower()
	if "fake" in lowered:
		return "#FF4B4B"
	if "suspicious" in lowered:
		return "#FFD700"
	if "real" in lowered:
		return "#00FF7F"
	return "#00FFFF"


def accent_for_verdict(verdict: str) -> str:
	if verdict == "Likely Fake":
		return "#FF4B4B"
	if verdict == "Suspicious":
		return "#FFD700"
	if verdict == "Likely Real":
		return "#00FF7F"
	return "#00FFFF"


def _section_value(text: str, key: str) -> str:
	match = re.search(rf"{re.escape(key)}\s*[:\-]\s*(.+)", text, re.IGNORECASE)
	return match.group(1).strip() if match else ""


def _append_optional_line(lines: list[str], label: str, value: object) -> None:
	text = _as_text(value).strip()
	if text:
		lines.append(f"**{label}:** {text}")


def _find_value(data: dict, keys: list[str]) -> object:
	for key in keys:
		if key in data:
			return data[key]
	return None


def build_readable_markdown(text: object, confidence: int, reality: int, verdict: str) -> str:
	data = try_parse_json(text)

	if data:
		claim = _find_value(data, ["claim", "core_claim"])
		explanation = _find_value(data, ["explanation", "reasoning", "summary"])
		evidence = data.get("evidence", [])
		content_type = _find_value(data, ["content_type", "contentType"])
		claim_source = _find_value(data, ["claim_source", "source_account", "source"])
		claim_entities = _find_value(data, ["claim_entities", "entities"])
		has_embedded_image = _find_value(data, ["has_embedded_image", "hasEmbeddedImage"])
		platform_signals = _find_value(data, ["platform_signals", "platformSignals"])
		extracted_text = _find_value(data, ["extracted_text", "ocr_text", "visible_text"])
		flags = _find_value(data, ["flags", "red_flags"])
		search_notes = _find_value(data, ["search_notes", "search_summary"])

		lines = [
			"## RealityLens Summary",
			f"**Verdict:** {verdict}",
			f"**Confidence:** {confidence}%",
			f"**Reality:** {reality}%",
		]

		_append_optional_line(lines, "Content Type", content_type)
		_append_optional_line(lines, "Claim Source", claim_source)
		_append_optional_line(lines, "Has Embedded Image", has_embedded_image)

		if claim_entities:
			lines += ["", "### Claim Entities", _as_text(claim_entities)]

		if platform_signals:
			lines += ["", "### Platform Signals", _as_text(platform_signals)]

		if claim:
			lines += ["", "### Claim", _as_text(claim)]

		if explanation:
			lines += ["", "### Explanation", _as_text(explanation)]

		if extracted_text:
			lines += ["", "### Extracted Text", _as_text(extracted_text)]

		if flags:
			lines += ["", "### Red Flags", _as_text(flags)]

		if search_notes:
			lines += ["", "### Search Notes", _as_text(search_notes)]

		if evidence:
			lines.append("")
			lines.append("### Evidence")
			for item in evidence:
				if isinstance(item, dict):
					title = str(item.get("title") or item.get("headline") or "Untitled source")
					url = str(item.get("url") or "").strip()
					stance = str(item.get("stance") or "").strip()
					source = str(item.get("source") or "").strip()
					details = " | ".join(part for part in [source, stance] if part)

					if url:
						line = f"- [{title}]({url})"
					else:
						line = f"- {title}"

					if details:
						line = f"{line} ({details})"
					lines.append(line)
				else:
					lines.append(f"- {_as_text(item)}")

		known_keys = {
			"claim", "core_claim", "reality_score", "confidence", "verdict", "explanation", "reasoning", "summary",
			"evidence", "content_type", "contentType", "claim_source", "source_account", "source",
			"claim_entities", "entities", "has_embedded_image", "hasEmbeddedImage", "platform_signals",
			"platformSignals", "extracted_text", "ocr_text", "visible_text", "flags", "red_flags",
			"search_notes", "search_summary"
		}
		additional = {k: v for k, v in data.items() if k not in known_keys and v not in (None, "", [], {})}
		if additional:
			lines += ["", "### Additional Details", "```json", json.dumps(additional, ensure_ascii=False, indent=2), "```"]

		return "\n".join(lines)

	raw_text = _as_text(text).strip() or "No analysis details available."
	return "\n".join([
		"## RealityLens Summary",
		f"**Verdict:** {verdict}",
		f"**Confidence:** {confidence}%",
		f"**Reality:** {reality}%",
		"",
		"### Raw Response",
		raw_text,
	])


class AnalyzerWorker(QObject):
    # Change 'str' to 'object' to allow dictionaries
    finished = pyqtSignal(object) 

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self):
        # verify_content now returns a dict, which 'object' accepts
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
	def __init__(self, data: object):
		super().__init__()    
        
		if isinstance(data, dict):
			self.result_text = json.dumps(data, indent=2)
		else:
			self.result_text = str(data)

		reality_score, confidence_score = extract_scores(data)
		parsed_verdict = extract_verdict_label(data)
		if parsed_verdict == "Analysis Complete":
			parsed_verdict = verdict_from_score(reality_score)
		self.display_verdict = parsed_verdict
		self.border_color = accent_for_verdict(parsed_verdict)

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

		self.subtitle = QLabel("")
		self.subtitle.setObjectName("SubLabel")
		content_layout.addWidget(self.subtitle)

		reality_row = QHBoxLayout()
		reality_label = QLabel("Reality Score")
		reality_label.setObjectName("SubLabel")
		reality_row.addWidget(reality_label)

		self.reality_meter = QProgressBar()
		self.reality_meter.setObjectName("TrustMeter")
		self.reality_meter.setRange(0, 100)
		self.reality_meter.setValue(reality_score)
		self.reality_meter.setTextVisible(False)
		self.reality_meter.setToolTip("Model reality score")
		reality_row.addWidget(self.reality_meter, 1)

		self.reality_score_label = QLabel("")
		self.reality_score_label.setObjectName("SubLabel")
		reality_row.addWidget(self.reality_score_label)
		content_layout.addLayout(reality_row)

		confidence_row = QHBoxLayout()
		confidence_label = QLabel("Confidence Score")
		confidence_label.setObjectName("SubLabel")
		confidence_row.addWidget(confidence_label)

		self.confidence_meter = QProgressBar()
		self.confidence_meter.setObjectName("TrustMeter")
		self.confidence_meter.setRange(0, 100)
		self.confidence_meter.setValue(confidence_score)
		self.confidence_meter.setTextVisible(False)
		self.confidence_meter.setToolTip("Model confidence score")
		confidence_row.addWidget(self.confidence_meter, 1)

		self.confidence_score_label = QLabel("")
		self.confidence_score_label.setObjectName("SubLabel")
		confidence_row.addWidget(self.confidence_score_label)
		content_layout.addLayout(confidence_row)

		self.body = QTextBrowser()
		self.body.setObjectName("BodyEdit")
		self.body.setOpenExternalLinks(True)
		self.body.setReadOnly(True)
		self.body.setMarkdown(build_readable_markdown(data, confidence_score, reality_score, parsed_verdict))
		content_layout.addWidget(self.body, 1)

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
		self.on_scores_changed(reality_score, confidence_score)
		self.move_to_bottom_right()

	def on_scores_changed(self, reality: int, confidence: int):
		verdict = getattr(self, "display_verdict", verdict_from_score(reality))
		self.subtitle.setText(f"{verdict} • Reality {reality}% • Confidence {confidence}%")
		self.reality_meter.setValue(reality)
		self.confidence_meter.setValue(confidence)
		self.reality_score_label.setText(f"{reality}%")
		self.confidence_score_label.setText(f"{confidence}%")
