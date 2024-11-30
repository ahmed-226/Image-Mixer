import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QComboBox
)
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt


class ImageGroup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel("Image", self)
        self.label.setMaximumWidth(400)
        self.label.setMinimumWidth(300)
        self.label.setMaximumHeight(400)
        self.label.setStyleSheet("border: 1px solid black;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label.setObjectName("image_label")

        self.canvas_group = QVBoxLayout()

        self.combo_box = QComboBox(self)
        self.combo_box.addItem("Magnitude")
        self.combo_box.addItem("Phase")
        self.combo_box.currentIndexChanged.connect(self.update_canvas)

        self.canvas = FigureCanvas(Figure(figsize=(4, 4)))

        self.canvas_group.addWidget(self.combo_box)
        self.canvas_group.addWidget(self.canvas)

        self.layout.addWidget(self.label)
        self.layout.addLayout(self.canvas_group)

        self.setLayout(self.layout)

        self.magnitude_spectrum = None
        self.phase_spectrum = None

    def update_canvas(self):
        if self.magnitude_spectrum is not None and self.phase_spectrum is not None:
            if self.combo_box.currentText() == "Magnitude":
                self.show_fft(self.magnitude_spectrum)
            else:
                self.show_fft(self.phase_spectrum)

    def show_fft(self, spectrum):
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.imshow(spectrum, cmap='gray')
        ax.axis('off')
        self.canvas.draw()


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Image FFT Viewer")
        self.setGeometry(100, 100, 1200, 400)

        h_layout1 = QHBoxLayout()
        h_layout2 = QHBoxLayout()

        self.image_group1 = ImageGroup(self)
        self.image_group2 = ImageGroup(self)
        self.image_group3 = ImageGroup(self)
        self.image_group4 = ImageGroup(self)

        h_layout1.addWidget(self.image_group1)
        h_layout1.addWidget(self.image_group2)

        h_layout2.addWidget(self.image_group3)
        h_layout2.addWidget(self.image_group4)

        self.image_group1.label.mouseDoubleClickEvent = lambda event: self.load_image(self.image_group1)
        self.image_group2.label.mouseDoubleClickEvent = lambda event: self.load_image(self.image_group2)
        self.image_group3.label.mouseDoubleClickEvent = lambda event: self.load_image(self.image_group3)
        self.image_group4.label.mouseDoubleClickEvent = lambda event: self.load_image(self.image_group4)

        main_layout = QVBoxLayout()
        main_layout.addLayout(h_layout1)
        main_layout.addLayout(h_layout2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_image(self, image_group):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if file_path:
            image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            self.show_image(image, image_group.label)

            f = np.fft.fft2(image)
            fshift = np.fft.fftshift(f)
            image_group.magnitude_spectrum = 20 * np.log(np.abs(fshift))
            image_group.phase_spectrum = np.angle(fshift)

            image_group.update_canvas()

    def show_image(self, image, label):
        h, w = image.shape
        qimage = QImage(image.data, w, h, w, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        label.setPixmap(pixmap)
        label.setScaledContents(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWidget()
    ex.show()
    sys.exit(app.exec_())