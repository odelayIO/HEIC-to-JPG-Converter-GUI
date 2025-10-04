import sys
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List, Dict, Optional
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QCheckBox, QSpinBox, QProgressBar, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# ------------------------ Conversion Functions ------------------------ #

def convert_single_file(heic_path: str, jpg_path: str, output_quality: int, resize: Optional[Tuple[int, int]] = None) -> Tuple[str, bool, float]:
    start_time = time.time()
    try:
        with Image.open(heic_path) as image:
            if resize:
                image = image.resize(resize, Image.LANCZOS)
            exif_data = image.info.get("exif")
            image.save(jpg_path, "JPEG", quality=output_quality, exif=exif_data, optimize=True)
            heic_stat = os.stat(heic_path)
            os.utime(jpg_path, (heic_stat.st_atime, heic_stat.st_mtime))
            processing_time = time.time() - start_time
            return heic_path, True, processing_time
    except (UnidentifiedImageError, FileNotFoundError, OSError) as e:
        processing_time = time.time() - start_time
        return heic_path, False, processing_time

def find_heic_files(directory: str, recursive: bool = False) -> List[str]:
    heic_files = []
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.heic', '.heif')):
                    heic_files.append(os.path.join(root, file))
    else:
        heic_files = [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if file.lower().endswith(('.heic', '.heif'))
        ]
    return heic_files

def convert_heic_to_jpg(
    heic_dir: str, 
    output_quality: int = 90, 
    max_workers: int = 4,
    output_dir: Optional[str] = None,
    recursive: bool = False,
    resize: Optional[Tuple[int, int]] = None,
    delete_originals: bool = False,
    progress_callback=None
) -> Dict:
    start_time = time.time()
    register_heif_opener()

    if not os.path.isdir(heic_dir):
        return {"status": "error", "message": f"Directory '{heic_dir}' does not exist."}

    if output_dir is None:
        jpg_dir = os.path.join(heic_dir, "ConvertedFiles")
    else:
        jpg_dir = output_dir

    if os.path.exists(jpg_dir):
        shutil.rmtree(jpg_dir)
    os.makedirs(jpg_dir, exist_ok=True)

    heic_files = find_heic_files(heic_dir, recursive=recursive)
    tasks = []

    for heic_path in heic_files:
        if recursive:
            rel_path = os.path.relpath(heic_path, heic_dir)
            jpg_path = os.path.join(jpg_dir, os.path.splitext(rel_path)[0] + ".jpg")
            os.makedirs(os.path.dirname(jpg_path), exist_ok=True)
        else:
            file_name = os.path.basename(heic_path)
            jpg_path = os.path.join(jpg_dir, os.path.splitext(file_name)[0] + ".jpg")
        if os.path.exists(jpg_path):
            continue
        tasks.append((heic_path, jpg_path))

    num_converted = 0
    failed_files = []
    total_processing_time = 0.0

    if not tasks:
        return {"status": "completed", "files_converted": 0, "message": "No new files to convert."}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(convert_single_file, heic_path, jpg_path, output_quality, resize): heic_path for heic_path, jpg_path in tasks}
        num_done = 0
        for future in as_completed(future_to_file):
            heic_file = future_to_file[future]
            try:
                heic_path, success, proc_time = future.result()
                total_processing_time += proc_time

                if success:
                    num_converted += 1
                    if delete_originals:
                        os.remove(heic_path)
                else:
                    failed_files.append(os.path.basename(heic_path))

                num_done += 1
                progress = int((num_done / len(tasks)) * 100)
                if progress_callback:
                    progress_callback(num_done, len(tasks), os.path.basename(heic_path), progress)
            except Exception as e:
                failed_files.append(os.path.basename(heic_file))
                num_done += 1
                if progress_callback:
                    progress_callback(num_done, len(tasks), os.path.basename(heic_file), int((num_done/len(tasks))*100))

    total_time = time.time() - start_time
    avg_time_per_file = total_processing_time / len(tasks) if tasks else 0

    return {
        "status": "completed",
        "files_converted": num_converted,
        "files_failed": len(failed_files),
        "total_time": total_time,
        "avg_time_per_file": avg_time_per_file,
        "failed_files": failed_files
    }

# ------------------------ PyQt GUI ------------------------ #

class WorkerThread(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(dict)

    def __init__(self, heic_dir, output_dir, quality, workers, recursive, resize, delete_originals):
        super().__init__()
        self.heic_dir = heic_dir
        self.output_dir = output_dir
        self.quality = quality
        self.workers = workers
        self.recursive = recursive
        self.resize = resize
        self.delete_originals = delete_originals

    def run(self):
        def progress_callback(done, total, filename, percent):
            self.progress_signal.emit(percent, filename)

        result = convert_heic_to_jpg(
            heic_dir=self.heic_dir,
            output_quality=self.quality,
            max_workers=self.workers,
            output_dir=self.output_dir,
            recursive=self.recursive,
            resize=self.resize,
            delete_originals=self.delete_originals,
            progress_callback=progress_callback
        )
        self.finished_signal.emit(result)

class HeicConverterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HEIC to JPG Converter")
        self.setGeometry(200, 200, 600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.src_label = QLabel("HEIC Directory:")
        self.src_input = QLineEdit()
        self.src_btn = QPushButton("Browse")
        self.src_btn.clicked.connect(self.browse_src)
        src_layout = QHBoxLayout()
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(self.src_btn)

        self.out_label = QLabel("Output Directory (optional):")
        self.out_input = QLineEdit()
        self.out_btn = QPushButton("Browse")
        self.out_btn.clicked.connect(self.browse_out)
        out_layout = QHBoxLayout()
        out_layout.addWidget(self.out_input)
        out_layout.addWidget(self.out_btn)

        self.quality_label = QLabel("Output Quality (1-100):")
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(90)

        self.workers_label = QLabel("Parallel Workers:")
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(4)

        self.recursive_cb = QCheckBox("Search Subdirectories")
        self.delete_cb = QCheckBox("Delete Original HEIC Files")

        self.resize_label = QLabel("Resize (WIDTHxHEIGHT):")
        self.resize_input = QLineEdit()

        self.start_btn = QPushButton("Start Conversion")
        self.start_btn.clicked.connect(self.start_conversion)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        layout.addWidget(self.src_label)
        layout.addLayout(src_layout)
        layout.addWidget(self.out_label)
        layout.addLayout(out_layout)
        layout.addWidget(self.quality_label)
        layout.addWidget(self.quality_spin)
        layout.addWidget(self.workers_label)
        layout.addWidget(self.workers_spin)
        layout.addWidget(self.recursive_cb)
        layout.addWidget(self.delete_cb)
        layout.addWidget(self.resize_label)
        layout.addWidget(self.resize_input)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def browse_src(self):
        folder = QFileDialog.getExistingDirectory(self, "Select HEIC Directory")
        if folder:
            self.src_input.setText(folder)

    def browse_out(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.out_input.setText(folder)

    def start_conversion(self):
        heic_dir = self.src_input.text()
        if not heic_dir or not os.path.isdir(heic_dir):
            self.log_output.append("Please select a valid HEIC directory.")
            return

        output_dir = self.out_input.text() or None
        quality = self.quality_spin.value()
        workers = self.workers_spin.value()
        recursive = self.recursive_cb.isChecked()
        delete_originals = self.delete_cb.isChecked()

        resize = None
        resize_text = self.resize_input.text().strip()
        if resize_text:
            try:
                width, height = map(int, resize_text.lower().split('x'))
                resize = (width, height)
            except ValueError:
                self.log_output.append("Invalid resize format. Use WIDTHxHEIGHT (e.g., 1920x1080).")
                return

        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_output.append("Starting conversion...")

        self.worker = WorkerThread(
            heic_dir, output_dir, quality, workers, recursive, resize, delete_originals
        )
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.conversion_finished)
        self.worker.start()

    def update_progress(self, percent, filename):
        self.progress_bar.setValue(percent)
        self.log_output.append(f"[{percent}%] Converted: {filename}")
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def conversion_finished(self, result):
        self.start_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.log_output.append("Conversion finished.")
        self.log_output.append(f"Status: {result.get('status')}")
        self.log_output.append(f"Files converted: {result.get('files_converted', 0)}")
        if result.get("files_failed"):
            self.log_output.append(f"Files failed: {result.get('files_failed')}")
            self.log_output.append(f"Failed files: {', '.join(result.get('failed_files', []))}")
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

# ------------------------ Main ------------------------ #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = HeicConverterGUI()
    gui.show()
    sys.exit(app.exec_())

