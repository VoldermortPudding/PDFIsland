import sys
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageEnhance, ImageOps
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


@dataclass
class ColorSettings:
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    invert: bool = False


class PDFIslandWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDFIsland - PDFium Reader")
        self.resize(1300, 850)

        self.pdf_doc: pdfium.PdfDocument | None = None
        self.current_page_index = 0
        self.zoom_scale = 1.0
        self.double_view = False
        self.color_settings = ColorSettings()

        self._init_ui()

    def _init_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        controls_row = QHBoxLayout()

        self.open_button = QPushButton("Open PDF")
        self.open_button.clicked.connect(self.open_pdf)
        controls_row.addWidget(self.open_button)

        self.prev_button = QPushButton("◀ Prev")
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        controls_row.addWidget(self.prev_button)

        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        controls_row.addWidget(self.next_button)

        self.page_label = QLabel("Page: - / -")
        controls_row.addWidget(self.page_label)

        controls_row.addWidget(QLabel("Zoom"))
        self.zoom_slider = self._make_slider(25, 400, 100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        controls_row.addWidget(self.zoom_slider)

        self.view_mode_button = QPushButton("Single")
        self.view_mode_button.clicked.connect(self.toggle_view_mode)
        self.view_mode_button.setEnabled(False)
        controls_row.addWidget(self.view_mode_button)

        controls_row.addStretch()
        root.addLayout(controls_row)

        color_row = QHBoxLayout()

        color_row.addWidget(QLabel("Brightness"))
        self.brightness_slider = self._make_slider(20, 300, 100)
        self.brightness_slider.valueChanged.connect(self.on_color_changed)
        color_row.addWidget(self.brightness_slider)

        color_row.addWidget(QLabel("Contrast"))
        self.contrast_slider = self._make_slider(20, 300, 100)
        self.contrast_slider.valueChanged.connect(self.on_color_changed)
        color_row.addWidget(self.contrast_slider)

        color_row.addWidget(QLabel("Saturation"))
        self.saturation_slider = self._make_slider(0, 300, 100)
        self.saturation_slider.valueChanged.connect(self.on_color_changed)
        color_row.addWidget(self.saturation_slider)

        self.invert_checkbox = QCheckBox("Invert colors")
        self.invert_checkbox.stateChanged.connect(self.on_color_changed)
        color_row.addWidget(self.invert_checkbox)

        self.reset_colors_button = QPushButton("Reset colors")
        self.reset_colors_button.clicked.connect(self.reset_colors)
        color_row.addWidget(self.reset_colors_button)

        root.addLayout(color_row)

        self.status_label = QLabel("Open a PDF to begin.")
        root.addWidget(self.status_label)

        self.viewer_container = QWidget()
        self.viewer_layout = QHBoxLayout(self.viewer_container)

        self.left_page_label = QLabel("No PDF loaded")
        self.left_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_page_label.setMinimumSize(600, 700)
        self.left_page_label.setStyleSheet("background:#1f1f1f; color:#efefef;")

        self.right_page_label = QLabel("")
        self.right_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_page_label.setMinimumSize(600, 700)
        self.right_page_label.setStyleSheet("background:#1f1f1f; color:#efefef;")
        self.right_page_label.hide()

        self.viewer_layout.addWidget(self.left_page_label)
        self.viewer_layout.addWidget(self.right_page_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.viewer_container)
        root.addWidget(scroll)

        self.setCentralWidget(central)

    @staticmethod
    def _make_slider(minimum: int, maximum: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        return slider

    def open_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        try:
            self.pdf_doc = pdfium.PdfDocument(path)
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "Failed to open PDF", str(error))
            self.pdf_doc = None
            return

        self.current_page_index = 0
        self.status_label.setText(f"Loaded: {Path(path).name}")
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.view_mode_button.setEnabled(True)
        self.render_current_view()

    def prev_page(self) -> None:
        if self.pdf_doc is None:
            return

        step = 2 if self.double_view else 1
        self.current_page_index = max(0, self.current_page_index - step)
        self.render_current_view()

    def next_page(self) -> None:
        if self.pdf_doc is None:
            return

        step = 2 if self.double_view else 1
        max_index = len(self.pdf_doc) - 1
        self.current_page_index = min(max_index, self.current_page_index + step)
        self.render_current_view()

    def toggle_view_mode(self) -> None:
        self.double_view = not self.double_view
        self.view_mode_button.setText("Double" if self.double_view else "Single")
        self.right_page_label.setVisible(self.double_view)
        self.render_current_view()

    def on_zoom_changed(self) -> None:
        self.zoom_scale = self.zoom_slider.value() / 100.0
        self.render_current_view()

    def on_color_changed(self) -> None:
        self.color_settings.brightness = self.brightness_slider.value() / 100.0
        self.color_settings.contrast = self.contrast_slider.value() / 100.0
        self.color_settings.saturation = self.saturation_slider.value() / 100.0
        self.color_settings.invert = self.invert_checkbox.isChecked()
        self.render_current_view()

    def reset_colors(self) -> None:
        self.brightness_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self.saturation_slider.setValue(100)
        self.invert_checkbox.setChecked(False)

    def render_current_view(self) -> None:
        if self.pdf_doc is None:
            return

        total = len(self.pdf_doc)
        left_index = min(self.current_page_index, total - 1)
        self._render_into_label(left_index, self.left_page_label)

        if self.double_view:
            right_index = left_index + 1
            if right_index < total:
                self._render_into_label(right_index, self.right_page_label)
            else:
                self.right_page_label.setText("(No next page)")
                self.right_page_label.setPixmap(QPixmap())

            shown_end = min(total, left_index + 2)
            self.page_label.setText(f"Pages: {left_index + 1}-{shown_end} / {total}")
        else:
            self.right_page_label.setPixmap(QPixmap())
            self.page_label.setText(f"Page: {left_index + 1} / {total}")

    def _render_into_label(self, page_index: int, label: QLabel) -> None:
        if self.pdf_doc is None:
            return

        page = self.pdf_doc[page_index]
        bitmap = page.render(scale=2.0 * self.zoom_scale)
        pil_image = bitmap.to_pil()
        adjusted = self.apply_color_settings(pil_image)

        qimage = ImageQt(adjusted)
        pixmap = QPixmap.fromImage(qimage)
        label.setPixmap(pixmap)
        label.setText("")

    def apply_color_settings(self, image: Image.Image) -> Image.Image:
        processed = image.convert("RGB")
        processed = ImageEnhance.Brightness(processed).enhance(self.color_settings.brightness)
        processed = ImageEnhance.Contrast(processed).enhance(self.color_settings.contrast)
        processed = ImageEnhance.Color(processed).enhance(self.color_settings.saturation)

        if self.color_settings.invert:
            processed = ImageOps.invert(processed)

        return processed


def main() -> None:
    app = QApplication(sys.argv)
    window = PDFIslandWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
