import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QInputDialog, QCheckBox,
                             QScrollArea, QGraphicsView, QGraphicsScene,
                             QGraphicsPixmapItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            factor = zoom_in_factor
        else:
            factor = zoom_out_factor

        self.scale(factor, factor)

class ImageAnnotator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Multi-Label Annotator")
        self.setGeometry(100, 100, 1200, 700)

        self.annotations = {}  
        self.index = 0
        self.image_folder = ""
        self.image_files = []
        self.classes = []
        self.save_path = None

        self.init_classes()
        if not self.classes:
            sys.exit()

        self.init_ui()
        self.load_folder()
        if self.image_files:
            self.show_image()
  # Custom save path

    def init_classes(self):
        text, ok = QInputDialog.getText(self, "Input Classes", "Enter initial class names separated by commas:")
        if ok and text:
            self.classes = [c.strip() for c in text.split(",") if c.strip()]

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        main_layout.addWidget(self.view, 3)

        panel = QVBoxLayout()
        main_layout.addLayout(panel, 1) 

        self.scroll = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scroll_widget)
        panel.addWidget(self.scroll)

        self.checkboxes = {}
        self.refresh_checkboxes()

        self.add_class_btn = QPushButton("Add Class")
        self.add_class_btn.clicked.connect(self.add_class)
        panel.addWidget(self.add_class_btn)

        self.choose_save_btn = QPushButton("Choose Save Location / Filename")
        self.choose_save_btn.clicked.connect(self.choose_save_location)
        panel.addWidget(self.choose_save_btn)

        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_image)
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_image)
        self.save_btn = QPushButton("Save JSON")
        self.save_btn.clicked.connect(self.save_json)

        panel.addWidget(self.prev_btn)
        panel.addWidget(self.next_btn)
        panel.addWidget(self.save_btn)

    def refresh_checkboxes(self):
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)

        self.checkboxes = {}
        for cls in self.classes:
            cb = QCheckBox(cls)
            self.scroll_layout.addWidget(cb)
            self.checkboxes[cls] = cb

        if self.image_files:
            current_file = self.image_files[self.index]
            selected_classes = self.annotations.get(current_file, [])
            for cls in selected_classes:
                if cls in self.checkboxes:
                    self.checkboxes[cls].setChecked(True)

    def add_class(self):
        text, ok = QInputDialog.getText(self, "Add New Class", "Class name:")
        if ok and text and text.strip():
            cls = text.strip()
            if cls not in self.classes:
                self.classes.append(cls)
                self.refresh_checkboxes()

    def choose_save_location(self):
        default_name = datetime.now().strftime("annotations_%Y%m%d_%H%M%S.json")
        path, _ = QFileDialog.getSaveFileName(self, "Select Save Location", default_name,
                                              "JSON Files (*.json)")
        if path:
            self.save_path = path

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.image_folder = folder
            self.image_files = [f for f in os.listdir(folder)
                                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.image_files.sort()

    def show_image(self):
        if not self.image_files:
            return
        path = os.path.join(self.image_folder, self.image_files[self.index])
        self.scene.clear()

        pil_img = Image.open(path)
        data = pil_img.convert("RGBA").tobytes("raw", "RGBA")
        qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

        current_file = self.image_files[self.index]
        selected_classes = self.annotations.get(current_file, [])
        for cls, cb in self.checkboxes.items():
            cb.setChecked(cls in selected_classes)

    def save_current_annotation(self):
        current_file = self.image_files[self.index]
        selected = [cls for cls, cb in self.checkboxes.items() if cb.isChecked()]
        self.annotations[current_file] = selected

    def next_image(self):
        self.save_current_annotation()
        if self.index < len(self.image_files) - 1:
            self.index += 1
            self.show_image()

    def prev_image(self):
        self.save_current_annotation()
        if self.index > 0:
            self.index -= 1
            self.show_image()

    def save_json(self):
        self.save_current_annotation()
        if self.save_path:
            path = self.save_path
        else:
            default_name = datetime.now().strftime("annotations_%Y%m%d_%H%M%S.json")
            path = os.path.join(os.getcwd(), default_name)

        with open(path, "w") as f:
            json.dump(self.annotations, f, indent=4)
        print(f"Saved annotations to {path}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ImageAnnotator()
    window.show()
    sys.exit(app.exec_())

