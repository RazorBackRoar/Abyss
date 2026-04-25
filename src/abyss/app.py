from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QIcon,
    QMouseEvent,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QWidget,
)

from abyss.processor import ProcessResult, process_paths
from abyss.sanitize import resolve_drop_path


def app_root() -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root)

    return Path(__file__).resolve().parents[2]


def asset_path(name: str) -> Path:
    return app_root() / "assets" / name


def icon() -> QIcon:
    for candidate in ("AppIcon.icns", "Abyss Icns.png"):
        path = asset_path(candidate)
        if path.exists():
            return QIcon(str(path))

    return QIcon()


class WorkerSignals(QObject):
    log = Signal(str)
    finished = Signal(list)


class ProcessWorker(QRunnable):
    def __init__(self, paths: list[Path]) -> None:
        super().__init__()
        self.paths = paths
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        results = process_paths(self.paths, progress=self.signals.log.emit)
        self.signals.finished.emit(results)


class AbyssCanvas(QWidget):
    paths_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.background = QPixmap(str(asset_path("abyss window.png")))
        self.drag_position: tuple[int, int] | None = None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: list[Path] = []

        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if not local_path:
                continue

            resolved = resolve_drop_path(local_path)
            if resolved is not None:
                paths.append(resolved)

        if paths:
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if self.background.isNull():
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
        else:
            painter.drawPixmap(self.rect(), self.background)

        super().paintEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            window_pos = self.window().frameGeometry().topLeft()
            self.drag_position = (
                global_pos.x() - window_pos.x(),
                global_pos.y() - window_pos.y(),
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drag_position and event.buttons() & Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            dx, dy = self.drag_position
            self.window().move(global_pos.x() - dx, global_pos.y() - dy)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.drag_position = None
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Abyss")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setFixedSize(960, 640)

        self.thread_pool = QThreadPool.globalInstance()
        self.active_workers = 0
        self.log_entries: list[str] = []

        app_icon = icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.canvas = AbyssCanvas()
        self.canvas.paths_dropped.connect(self.start_processing)
        self.setCentralWidget(self.canvas)

        self.status_panel = QLabel(self.canvas)
        self.status_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_panel.setTextFormat(Qt.TextFormat.RichText)
        self.status_panel.setStyleSheet(
            """
            QLabel {
                background: rgba(0, 0, 0, 150);
                border: 1px solid rgba(171, 255, 63, 120);
                border-radius: 18px;
                color: #f3f8ef;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display";
                font-size: 15px;
                padding: 8px 18px;
            }
            """
        )
        self.status_panel.hide()

        self.close_button = self.make_hotspot("Close", self.close)
        self.minimize_button = self.make_hotspot("Minimize", self.showMinimized)
        self.zoom_button = self.make_hotspot("Zoom", self.toggle_zoom)
        self.help_button = self.make_hotspot("Help", self.show_help)
        self.info_button = self.make_hotspot("Processing Log", self.show_log)

        self.position_overlays()

    def make_hotspot(self, label: str, callback) -> QPushButton:  # noqa: ANN001
        button = QPushButton("", self.canvas)
        button.setAccessibleName(label)
        button.setToolTip(label)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFlat(True)
        button.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(170, 255, 63, 35);
                border: 1px solid rgba(170, 255, 63, 110);
                border-radius: 14px;
            }
            """
        )
        button.clicked.connect(callback)
        return button

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        self.position_overlays()

    def position_overlays(self) -> None:
        width = self.canvas.width() or self.width()
        height = self.canvas.height() or self.height()

        def box(center_x: float, center_y: float, size: float) -> tuple[int, int, int, int]:
            side = int(width * size)
            return (
                int((center_x * width) - (side / 2)),
                int((center_y * height) - (side / 2)),
                side,
                side,
            )

        self.close_button.setGeometry(*box(0.148, 0.127, 0.035))
        self.minimize_button.setGeometry(*box(0.176, 0.127, 0.035))
        self.zoom_button.setGeometry(*box(0.205, 0.127, 0.035))
        self.help_button.setGeometry(*box(0.158, 0.839, 0.058))
        self.info_button.setGeometry(*box(0.839, 0.839, 0.058))
        self.status_panel.setGeometry(
            int(width * 0.28),
            int(height * 0.782),
            int(width * 0.44),
            int(height * 0.12),
        )

    def set_status(self, title: str, detail: str, color: str) -> None:
        self.status_panel.setText(
            f"<div><span style='color:{color}; font-size:18px;'>● {title}</span></div>"
            f"<div style='color:#e9eee6; margin-top:4px;'>{detail}</div>"
        )
        self.status_panel.show()

    def toggle_zoom(self) -> None:
        if self.isMaximized():
            self.showNormal()
            self.setFixedSize(960, 640)
        else:
            self.setMinimumSize(720, 480)
            self.setMaximumSize(16_000, 16_000)
            self.showMaximized()

    def show_help(self) -> None:
        QMessageBox.information(
            self,
            "Abyss",
            (
                "Drop files or folders onto the window.\n\n"
                "Images are rewritten as metadata-free JPEG files. Videos are remuxed "
                "or re-encoded as metadata-free MP4 files. Originals are removed only "
                "after a replacement is successfully written."
            ),
        )

    def show_log(self) -> None:
        message = "\n".join(self.log_entries[-80:]) if self.log_entries else "No jobs yet."
        QMessageBox.information(self, "Processing Log", message)

    @Slot(list)
    def start_processing(self, paths: list[Path]) -> None:
        if self.active_workers > 0:
            QMessageBox.warning(
                self,
                "Abyss is busy",
                "A job is already running. Wait for it to finish before dropping more files.",
            )
            return

        self.log_entries.clear()
        self.set_status("Processing", f"{len(paths)} dropped item(s)", "#aaff3f")
        self.active_workers += 1

        worker = ProcessWorker(paths)
        worker.signals.log.connect(self.append_log)
        worker.signals.finished.connect(self.processing_finished)
        self.thread_pool.start(worker)

    @Slot(str)
    def append_log(self, text: str) -> None:
        self.log_entries.append(text)

    @Slot(list)
    def processing_finished(self, results: list[ProcessResult]) -> None:
        self.active_workers = max(0, self.active_workers - 1)

        done = sum(1 for result in results if result.status == "done")
        skipped = sum(1 for result in results if result.status == "skipped")
        errors = sum(1 for result in results if result.status == "error")

        color = "#ffcc4d" if errors else "#aaff3f"
        self.set_status(
            "Finished",
            f"Done: {done} | Skipped: {skipped} | Errors: {errors}",
            color,
        )

        self.log_entries.append("")
        self.log_entries.append("Summary")
        self.log_entries.append("-------")
        self.log_entries.append(f"Done: {done}")
        self.log_entries.append(f"Skipped: {skipped}")
        self.log_entries.append(f"Errors: {errors}")


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Abyss")

    app_icon = icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    window = MainWindow()
    window.show()

    return app.exec()
