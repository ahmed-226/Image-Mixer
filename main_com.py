import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import QSizePolicy,QSpacerItem, QApplication, QFrame, QComboBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QSlider, QRadioButton, QButtonGroup
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector

class ImageData(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)



        self.image = None
        self.magnitude_spectrum = None
        self.phase_sepctrum = None
        self.transformed = None

        self.label = QLabel("Load Image", self.image)
        self.label.setObjectName("image_label")
        
        self.label.setMaximumWidth(300)
        self.label.setMinimumWidth(300)
        self.label.setMaximumHeight(300)
        self.label.setMinimumHeight(300)

        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("image_label")

        self.component_canvas = FigureCanvas(Figure(figsize=(2, 2)))
        self.component_canvas.setFixedSize(250, 300)
        self.ax = self.component_canvas.figure.add_subplot(111)
        self.ax.axis('off') 

        self.magnitude_radio = QRadioButton("Magnitude")
        self.magnitude_radio.setChecked(True)
        self.phase_radio = QRadioButton("Phase") 
        self.real_radio = QRadioButton("Real") 
        self.imaginary_radio = QRadioButton("Imaginary")  


        self.component_group = QButtonGroup(self)

        self.component_group.addButton(self.magnitude_radio)
        self.component_group.addButton(self.phase_radio)  
        self.component_group.addButton(self.real_radio)
        self.component_group.addButton(self.imaginary_radio) 

        self.component_group.buttonClicked.connect(self.update_component_display)

        H_radio_frame = QFrame()
        H_radio_frame.setObjectName("H_radio_frame")
        H_radio_layout = QHBoxLayout()
        H_radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        H_radio_layout.setSpacing(50)
        H_radio_frame.setLayout(H_radio_layout)
        H_radio_layout.addWidget(self.magnitude_radio)
        H_radio_layout.addWidget(self.phase_radio)
        H_radio_layout.addWidget(self.real_radio)
        H_radio_layout.addWidget(self.imaginary_radio)



        self.label.mouseDoubleClickEvent = lambda event: self.load_image()

        H_layout = QHBoxLayout()
        H_layout.addWidget(self.label)
        H_layout.addWidget(self.component_canvas)

        self.layout.addLayout(H_layout)
        self.layout.addSpacerItem(QSpacerItem(0,15,QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        self.layout.addWidget(H_radio_frame)

        self.setLayout(self.layout)
        self.rectangle_selector = RectangleSelector(
            self.ax,
            onselect=None,
            interactive=True,
            useblit=True,  
            drag_from_anywhere=True,
            spancoords = 'pixels'
                )
        self.rectangle_selector.set_active(True)

    def load_image(self, file_path=None):
        if file_path == None:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")

        if file_path:
            self.image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            self.image = cv2.resize(self.image, (300, 300))
            self.calculate_frequency_components()
            self.display_image(self.label)
            self.update_component_display()

    def calculate_frequency_components(self):
        if self.image is not None:
            self.transformed = np.fft.fft2(self.image)
            self.magnitude_spectrum = np.abs(self.transformed)
            self.phase_sepctrum = np.angle(self.transformed)



    def display_image(self, label):
        if self.image is not None:
            height, width = self.image.shape
            bytes_per_line = width
            image_bytes = self.image.tobytes()
            qimage = QImage(image_bytes, width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label.setPixmap(pixmap.scaled(label.width(), label.height(), Qt.KeepAspectRatio))  
            print(self.image)
            
    def update_component_display(self):
        if self.transformed is not None:
            fshift = np.fft.fftshift(self.transformed)
            if self.image is not None:
                if self.magnitude_radio.isChecked():
                    component = 20 * np.log(np.abs(fshift) + 1e-5)
                else:
                    component = np.angle(fshift)

                self.ax.clear()
                self.ax.imshow(component, cmap='gray')
                self.ax.axis('off')
                self.component_canvas.draw()
        else:
            print("Error: No transformed data available. Please load an image first.")


class outputPort(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
        self.label = QLabel("Output Port")
        self.label.setObjectName("reconstructed_label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.label.setMaximumWidth(300)
        self.label.setMinimumWidth(300)
        self.label.setMaximumHeight(300)
        self.label.setMinimumHeight(300)



        label_frame = QFrame()
        label_frame.setObjectName("label_frame")
        label_layout = QVBoxLayout()
        label_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_frame.setLayout(label_layout)

        label_layout.addWidget(self.label)

        self.layout.addWidget(label_frame)

        self.process_button=QPushButton("Reconstruct")
        self.process_button.setFixedHeight(50)
        self.layout.addWidget(self.process_button)

        

        self.weight_sliders = []
        self.combo_boxes = []

        for i in range(4):
            self.control_frame = QFrame()
            self.control_frame.setObjectName("control_frame")
            self.control_layout = QVBoxLayout()
            self.control_layout.setSpacing(20)

            self.control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)                 
            self.control_frame.setLayout(self.control_layout)

            H_layout = QHBoxLayout()
            
            self.percentage_label = QLabel("0%")
            self.percentage_label.setObjectName("percentage_label")

            self.weight_slider = QSlider(Qt.Orientation.Horizontal)
            self.weight_slider.setRange(0, 100)
            self.weight_slider.setValue(0)
            self.weight_slider.setTickInterval(1)
            self.weight_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.weight_slider.setFixedWidth(250)
            self.weight_slider.valueChanged.connect(lambda value, label=self.percentage_label: self.update_slider_label(value, label))
            self.weight_sliders.append(self.weight_slider)

            H_layout.addWidget(self.weight_slider)
            H_layout.addWidget(self.percentage_label)


            self.combo_box = QComboBox()
            self.combo_box.setFixedWidth(250)
            self.combo_box.addItem("Magnitude")
            self.combo_box.addItem("Phase")

            self.combo_boxes.append(self.combo_box)

            self.control_layout.addWidget(self.combo_box)
            self.control_layout.addLayout(H_layout)  
                  
            self.layout.addWidget(self.control_frame)

        self.setLayout(self.layout)

    def update_slider_label(self, value, label):
        label.setText(f"{value}%")


class ImageReconstructionApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Frequency Reconstruction with Weight Sliders")
        self.setGeometry(200, 200, 1000, 600)

        self.right_frame = QFrame()
        self.right_frame.setObjectName("right_frame")
        self.right_frame.setMaximumWidth(350)
        self.right_frame.setMinimumWidth(350)

        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)

        self.left_frame = QFrame()
        self.left_frame.setObjectName("left_frame")
        self.left_frame.setMaximumWidth(350)
        self.left_frame.setMinimumWidth(350)
        self.left_layout = QVBoxLayout()
        self.left_frame.setLayout(self.left_layout)

        self.middle_frame = QFrame()
        self.middle_frame.setObjectName("middle_frame")
        self.middle_layout = QVBoxLayout()
        self.middle_frame.setLayout(self.middle_layout)


        self.layout = QHBoxLayout()

        # Variables to store image objects
        self.image_1 = ImageData()
        self.image_2 = ImageData()
        self.image_3 = ImageData()
        self.image_4 = ImageData()

        self.output_port_1 = outputPort()
        self.output_port_2 = outputPort()

        images=[self.image_1, self.image_2, self.image_3, self.image_4]


        # Horizontal layout for displaying the images
        self.image_layout = QHBoxLayout()


        H_frame_1=QFrame()
        H_frame_1.setObjectName("H_frame_1")
        H_layout_1 = QHBoxLayout()
        H_layout_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        H_frame_1.setLayout(H_layout_1)
        H_layout_1.setContentsMargins(0, 0, 0, 0)


        H_frame_2=QFrame()
        H_frame_2.setObjectName("H_frame_2")
        H_layout_2 = QHBoxLayout()
        H_layout_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        H_layout_2.setContentsMargins(0, 0, 0, 0)

        H_frame_2.setLayout(H_layout_2)

        H_layout_1.addWidget(self.image_1)
        H_layout_1.addWidget(self.image_2)

        H_layout_2.addWidget(self.image_3)
        H_layout_2.addWidget(self.image_4)

        self.middle_layout.addWidget(H_frame_1)
        self.middle_layout.addWidget(H_frame_2)


        self.right_layout.addWidget(self.output_port_1)
        self.left_layout.addWidget(self.output_port_2)

        

        self.layout.addWidget(self.left_frame)
        self.layout.addWidget(self.middle_frame)
        self.layout.addWidget(self.right_frame)

        # Buttons for loading images and processing



        # Connect buttons to functions
        self.output_port_1.process_button.clicked.connect(lambda: self.process_images(self.output_port_1))
        self.output_port_2.process_button.clicked.connect(lambda: self.process_images(self.output_port_2))


        self.setLayout(self.layout)

        self.image_1.rectangle_selector.onselect = self.on_select
        self.image_2.rectangle_selector.onselect = self.on_select
        self.image_3.rectangle_selector.onselect = self.on_select
        self.image_4.rectangle_selector.onselect = self.on_select
        
        self.selected_region = [0,300,0,300]
        
        self.load_initial_images()

    def load_initial_images(self):
            image_paths = [
                'data/image1.jpg',
                'data/image2.jpg',
                'data/image3.jpg',
                'data/image4.jpg'
            ]
            images = [self.image_1, self.image_2, self.image_3, self.image_4]

            for image, path in zip(images, image_paths):
                ImageData.load_image(image, path)
                image.rectangle_selector.extents = (0, 300, 0, 300)
                image.rectangle_selector.update()

    def on_select(self, eclick, erelease):
            x0, y0 = round(eclick.xdata), round(eclick.ydata)
            x1, y1 = round(erelease.xdata), round(erelease.ydata)

            print(f"Normalized coordinates (x0, y0): ({x0}, {y0})")
            print(f"Normalized coordinates (x1, y1): ({x1}, {y1})")

            if x0 == x1 or y0 == y1:
                return
            self.selected_region = [y0, y1, x0, x1]

            for image in [self.image_1, self.image_2, self.image_3, self.image_4]:
                if image.magnitude_spectrum is not None:
                                       
                    image.rectangle_selector.extents = (x0, x1, y0, y1)
                    image.rectangle_selector.update()
                    
                    
    def process_images(self, output_port):
        images = [self.image_1, self.image_2, self.image_3, self.image_4]

        for image in images:
            if image.image is not None:
                image.calculate_frequency_components()

        if all(image.image is not None for image in images):
            magnitude_components = np.zeros_like(images[0].magnitude_spectrum[
                    self.selected_region[0] : self.selected_region[1],
                    self.selected_region[2] : self.selected_region[3]])
            phase_components = np.zeros_like(images[0].phase_sepctrum[
                    self.selected_region[0] : self.selected_region[1],
                    self.selected_region[2] : self.selected_region[3]])


            for i in range(4):
                if output_port.combo_boxes[i].currentText() == "Magnitude":
                    magnitude_components += (output_port.weight_sliders[i].value() / 100.0) * images[i].magnitude_spectrum[
                    self.selected_region[0] : self.selected_region[1],
                    self.selected_region[2] : self.selected_region[3]]
                    
                    
                elif output_port.combo_boxes[i].currentText() == "Phase":
                    phase_components += (output_port.weight_sliders[i].value() / 100.0) * images[i].phase_sepctrum[
                    self.selected_region[0] : self.selected_region[1],
                    self.selected_region[2] : self.selected_region[3]]
                   
                print(images[0].magnitude_spectrum[
                    self.selected_region[0] : self.selected_region[1],
                    self.selected_region[2] : self.selected_region[3]])
                
                print(f'mag components  {magnitude_components}')
                print(f'phase components {phase_components}')
                print(images[1].phase_sepctrum[
                    self.selected_region[0] : self.selected_region[1],
                    self.selected_region[2] : self.selected_region[3]])

            total_magnitude_weight = sum(output_port.weight_sliders[i].value() for i in range(4) if output_port.combo_boxes[i].currentText() == "Magnitude") / 100.0
            total_phase_weight = sum(output_port.weight_sliders[i].value() for i in range(4) if output_port.combo_boxes[i].currentText() == "Phase") / 100.0
            print(f"sum mag {total_magnitude_weight}")
            print(f"sum phase {total_phase_weight}")

            if total_magnitude_weight > 0:
                magnitude_components /= total_magnitude_weight
            if total_phase_weight > 0:
                phase_components /= total_phase_weight
            print(f"total mag {magnitude_components}")
            print(f"total phase {phase_components}")

            reconstructed_f = magnitude_components * np.exp(1j * phase_components)
            reconstructed_image = np.abs(np.fft.ifft2(reconstructed_f))
            print(f"reconstructed image before{reconstructed_image}")
            reconstructed_image = np.uint8(np.clip(reconstructed_image, 0, 255))
            print(f"reconstructed image after{reconstructed_image}")

            height, width = reconstructed_image.shape
            bytes_per_line = width
            image_bytes = reconstructed_image.tobytes()
            qimage = QImage(image_bytes, width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            output_port.label.setPixmap(pixmap.scaled(output_port.label.width(), output_port.label.height(), Qt.KeepAspectRatio))  # Resize to fit label

        else:
            print("Please load images.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    with open("./Styling/style.css", "r") as file:
        app.setStyleSheet(file.read())
    
    window = ImageReconstructionApp()
    window.show()
    sys.exit(app.exec_())