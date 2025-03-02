import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import QSizePolicy,QSpacerItem, QProgressBar, QApplication, QFrame, QComboBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QSlider, QRadioButton, QButtonGroup
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
# import logging
# # Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageData(QWidget):
    def __init__(self):
        super().__init__()
        # logging.debug("Initializing ImageData")
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)



        self.image = None
        self.magnitude_spectrum = None
        self.phase_spectrum = None
        self.real_spectrum = None
        self.imaginary_spectrum = None
        self.transformed = None
        self.brightness = 0  
        self.contrast = 1.0  
        self.start_pos = None        

        self.label = QLabel("Load Image", self.image)
        self.label.setObjectName("image_label")

        self.label.mousePressEvent = self.start_mouse_drag
        self.label.mouseMoveEvent = self.adjust_brightness_contrast
        
        self.label.setMaximumWidth(250)
        self.label.setMinimumWidth(250)
        self.label.setMaximumHeight(250)
        self.label.setMinimumHeight(250)

        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("image_label")

        self.component_canvas = FigureCanvas(Figure(figsize=(2, 2)))
        self.component_canvas.setFixedSize(250, 250)
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

        # Add Clear Image button
        self.clear_button = QPushButton("Clear Image")
        self.clear_button.clicked.connect(self.clear_image)
        self.layout.addWidget(self.clear_button)

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

    def clear_image(self):
        '''Clear the image and set it to black'''
        self.image = np.zeros((250, 250), dtype=np.uint8)
        self.calculate_frequency_components()
        self.display_image(self.label)
        self.update_component_display()

    def start_mouse_drag(self, event):
        '''Start tracking the mouse drag'''
        # logging.debug("Adjusting brightness and contrast")
        self.start_pos = event.pos()

    def adjust_brightness_contrast(self, event):
        '''Adjust brightness and contrast based on mouse movement'''
        # logging.debug("Adjusting brightness and contrast")

        if self.image is None:
            return

        dx = event.pos().x() - self.start_pos.x()  
        dy = event.pos().y() - self.start_pos.y()  
        
        self.brightness = dy * 0.5  
        self.contrast = 1 + (dx * 0.01)  

        adjusted_image = self.apply_brightness_contrast(self.image, self.brightness, self.contrast)

        h, w = adjusted_image.shape
        qimage = QImage(adjusted_image.data, w, h, w, QImage.Format.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)

        self.update_component_due_brightness_contrast(adjusted_image)

    def apply_brightness_contrast(self, image, brightness, contrast):
        
        '''Apply brightness and contrast adjustments'''
        # logging.debug(f"Applying brightness {brightness} and contrast {contrast}")
    
        adjusted = np.clip(contrast * image + brightness, 0, 255).astype(np.uint8)
        return adjusted

    def load_image(self, file_path=None):
        # logging.debug(f"Loading image from {file_path}")
    
        if file_path == None:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")

        if file_path:
            self.image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            self.image = cv2.resize(self.image, (250, 250))
            self.calculate_frequency_components()
            self.display_image(self.label)
            self.update_component_display()

    def calculate_frequency_components(self):
        # logging.debug("Calculating frequency components")

        if self.image is not None:
            self.transformed = np.fft.fftshift(np.fft.fft2(self.image))
            self.magnitude_spectrum = np.abs(self.transformed)
            self.phase_spectrum = np.angle(self.transformed)
            self.real_spectrum = np.real(self.transformed)
            self.imaginary_spectrum = np.imag(self.transformed)

    def display_image(self, label):
        # logging.debug("Displaying image")

        if self.image is not None:
            height, width = self.image.shape
            bytes_per_line = width
            image_bytes = self.image.tobytes()
            qimage = QImage(image_bytes, width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label.setPixmap(pixmap.scaled(label.width(), label.height(), Qt.KeepAspectRatio))  

    def update_component_due_brightness_contrast(self, image):
        # logging.debug("Updating component due to brightness and contrast adjustment")

        if image is not None:
            if not isinstance(image, np.ndarray) or len(image.shape) != 2:
                return
            if image.size == 0:
                return
            
            f = np.fft.fft2(image)
            fshift = np.fft.fftshift(f)
            self.transformed = fshift
            self.magnitude_spectrum = np.abs(self.transformed)
            self.phase_spectrum = np.angle(self.transformed)
            self.real_spectrum = np.real(self.transformed)
            self.imaginary_spectrum = np.imag(self.transformed)

        if self.image is not None:
            if self.magnitude_radio.isChecked():
                component = 20 * np.log(np.abs(fshift) + 1e-5)
            elif self.phase_radio.isChecked():
                component = np.angle(fshift)
            elif self.real_radio.isChecked():
                component = np.real(fshift)
            elif self.imaginary_radio.isChecked():
                component = np.imag(fshift)

            self.ax.clear()
            self.ax.imshow(component, cmap='gray')
            self.ax.axis('off')
            self.component_canvas.draw()

            
    def update_component_display(self):
        """Update the displayed frequency component based on the selected radio button."""
        # logging.debug("Updating component display")

        current_image = self.image
        if current_image is None:
            return

       

        if self.magnitude_radio.isChecked():
            component = 20 * np.log(self.magnitude_spectrum+ 1e-5)
        elif self.phase_radio.isChecked():
            component = self.phase_spectrum
        elif self.real_radio.isChecked():
            component = self.real_spectrum
        elif self.imaginary_radio.isChecked():
            component = self.imaginary_spectrum

        # Update the plot
        self.ax.clear()
        self.ax.imshow(component, cmap='gray')
        self.ax.axis('off')
        self.component_canvas.draw()




class outputPort(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        # logging.debug("Initializing outputPort")

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
            self.combo_box.addItem("Real")
            self.combo_box.addItem("Imaginary")

            self.combo_boxes.append(self.combo_box)

            self.control_layout.addWidget(self.combo_box)
            self.control_layout.addLayout(H_layout)  
                  
            self.layout.addWidget(self.control_frame)
        self.mode_group = QButtonGroup(self)

        self.magnitude_phase_mode = QRadioButton("Magnitude / Phase", self)
        self.magnitude_phase_mode.setChecked(True)
        self.mode_group.addButton(self.magnitude_phase_mode)
        
        self.real_imaginary_mode = QRadioButton("Real / Imaginary", self)
        self.real_imaginary_mode.setChecked(False)

        self.mode_group.addButton(self.real_imaginary_mode)
       
        self.layout.addWidget(self.magnitude_phase_mode)
        self.layout.addWidget(self.real_imaginary_mode)
        
        
        
        self.region_group = QButtonGroup(self)

        self.inside_region_radio = QRadioButton("Region inside", self)
        self.inside_region_radio.setChecked(True)
        self.region_group.addButton(self.inside_region_radio)
        
        self.outside_region_radio = QRadioButton("Region outside", self)
        self.outside_region_radio.setChecked(False)

        self.region_group.addButton(self.outside_region_radio)
       
        self.layout.addWidget(self.inside_region_radio)
        self.layout.addWidget(self.outside_region_radio)
       
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("Loading: %p%")  
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)

    def update_slider_label(self, value, label):
        # logging.debug(f"Updating slider label to {value}%")
        label.setText(f"{value}%")


class ImageReconstructionApp(QWidget):
    def __init__(self):
        super().__init__()
        # logging.debug("Initializing ImageReconstructionApp")

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
########################
        self.current_output_port = self.output_port_1
        self.output_port_1_radio = QRadioButton()
        self.output_port_2_radio = QRadioButton()
        self.output_port_2_radio.setChecked(True)

        self.output_port_group = QButtonGroup()
        self.output_port_group.addButton(self.output_port_1_radio)
        self.output_port_group.addButton(self.output_port_2_radio)

        self.output_port_1_radio.toggled.connect(lambda: self.set_current_output_port(self.output_port_1))
        self.output_port_2_radio.toggled.connect(lambda: self.set_current_output_port(self.output_port_2))

        ###############################
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

        self.right_layout.addWidget(self.output_port_1_radio)
        self.right_layout.addWidget(self.output_port_1)
        self.left_layout.addWidget(self.output_port_2_radio)
        self.left_layout.addWidget(self.output_port_2)

        

        self.layout.addWidget(self.left_frame)
        self.layout.addWidget(self.middle_frame)
        self.layout.addWidget(self.right_frame)




        self.output_port_1.process_button.clicked.connect(lambda: self.process_images())
        self.output_port_2.process_button.clicked.connect(lambda: self.process_images())


        self.setLayout(self.layout)

        self.image_1.rectangle_selector.onselect = self.on_select
        self.image_2.rectangle_selector.onselect = self.on_select
        self.image_3.rectangle_selector.onselect = self.on_select
        self.image_4.rectangle_selector.onselect = self.on_select
        
        self.selected_region = [0,250,0,250]
        
        self.load_initial_images()
       
       
        for slider in self.current_output_port.weight_sliders:
            slider.valueChanged.connect(lambda: self.process_images())
        for combo_box in self.current_output_port.combo_boxes:
            combo_box.currentIndexChanged.connect(lambda: self.process_images())
        self.current_output_port.magnitude_phase_mode.toggled.connect(lambda: self.process_images())
        self.current_output_port.real_imaginary_mode.toggled.connect(lambda: self.process_images())
        self.current_output_port.inside_region_radio.toggled.connect(lambda: self.process_images())
        self.current_output_port.outside_region_radio.toggled.connect(lambda: self.process_images())

        

   
    def set_current_output_port(self, output_port):
        self.current_output_port = output_port
        self.process_images()
         
    def load_initial_images(self):
            # logging.debug("Loading initial images")
    
            image_paths =  ['Data/image1.jpg',
           'Data/image2.jpg',
           'Data/image3.jpg',
          'Data/image4.jpg',
        ]
            images = [self.image_1, self.image_2, self.image_3, self.image_4]

            for image, path in zip(images, image_paths):
                image.load_image(path)
                image.rectangle_selector.extents = (0, 250, 0, 250)
                image.rectangle_selector.update()

    def on_select(self, eclick, erelease):
            # logging.debug("Selecting region")

            x0, y0 = round(eclick.xdata), round(eclick.ydata)
            x1, y1 = round(erelease.xdata), round(erelease.ydata)

            if x0 == x1 or y0 == y1:
                return
            self.selected_region = [y0, y1, x0, x1]

            for image in [self.image_1, self.image_2, self.image_3, self.image_4]:
                if image.magnitude_spectrum is not None:
                                       
                    image.rectangle_selector.extents = (x0, x1, y0, y1)
                    image.rectangle_selector.update()
                    self.process_images()
                    
    def get_outer_region(self, all_region, inner_region):
        print(f'all region shape {all_region.shape}')
        print(f'inner region shape {inner_region.shape}')
        padded_inner_region = np.pad(inner_region, ((0, all_region.shape[0] - inner_region.shape[0]),
                                            (0, all_region.shape[1] - inner_region.shape[1])),
                             mode='constant', constant_values=0)

        common_elements = np.isin(all_region, padded_inner_region)

        outer_region = np.where(common_elements, 0, all_region)
        print(f'outer region shape {outer_region.shape}')
        print(outer_region)
        return outer_region                        
    
                    
    def process_images(self):
        # logging.debug("Processing images")

        output_port = self.current_output_port
        output_port.progress_bar.setValue(20)
        
        images = [self.image_1, self.image_2, self.image_3, self.image_4]

        
        if output_port.inside_region_radio.isChecked():
            if all(image.image is not None for image in images):
                magnitude_components = np.zeros_like(images[0].magnitude_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])
                phase_components = np.zeros_like(images[0].phase_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])
                real_components = np.zeros_like(images[0].real_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])
                imaginary_components = np.zeros_like(images[0].imaginary_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])

                for i in range(4):
                    # logging.debug(f"Slider {i}: weight = {weight}, component = {component_type}")

                    weight = output_port.weight_sliders[i].value()
                    component_type = output_port.combo_boxes[i].currentText()
                    print(f"Slider {i}: weight = {weight}, component = {component_type}")

                    if component_type == "Magnitude":
                        magnitude_components += weight * images[i].magnitude_spectrum[
                            self.selected_region[0] : self.selected_region[1],
                            self.selected_region[2] : self.selected_region[3]]
                    elif component_type == "Phase":
                        phase_components += weight * images[i].phase_spectrum[
                            self.selected_region[0] : self.selected_region[1],
                            self.selected_region[2] : self.selected_region[3]]
                    elif component_type == "Real":
                        real_components += weight * images[i].real_spectrum[
                            self.selected_region[0] : self.selected_region[1],
                            self.selected_region[2] : self.selected_region[3]]
                    elif component_type == "Imaginary":
                        imaginary_components += weight * images[i].imaginary_spectrum[
                            self.selected_region[0] : self.selected_region[1],
                            self.selected_region[2] : self.selected_region[3]]
        else:
            if all(image.image is not None for image in images):
                magnitude_components = np.zeros_like(images[0].magnitude_spectrum[
                        0 : 250,
                        0 : 250])
                phase_components = np.zeros_like(images[0].phase_spectrum[
                        0 : 250,
                        0 : 250])
                real_components = np.zeros_like(images[0].real_spectrum[
                        0 : 250,
                        0 : 250])
                imaginary_components = np.zeros_like(images[0].imaginary_spectrum[
                        0 : 250,
                        0 : 250])


                for i in range(4):
                    weight = output_port.weight_sliders[i].value()
                    component_type = output_port.combo_boxes[i].currentText()
                    print(f"Slider {i}: weight = {weight}, component = {component_type}")
                    
                    if component_type == "Magnitude":
                        magnitude_components += weight* self.get_outer_region(images[i].magnitude_spectrum, images[i].magnitude_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])
                        
                    elif component_type == "Phase":                        
                        phase_components += weight * self.get_outer_region(images[i].phase_spectrum, images[i].phase_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])
                        
                    elif component_type == "Real":
                        real_components += weight * self.get_outer_region(images[i].real_spectrum, images[i].real_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])
                        
                    elif component_type == "Imaginary":
                        real_components += weight * self.get_outer_region(images[i].imaginary_spectrum, images[i].imaginary_spectrum[
                        self.selected_region[0] : self.selected_region[1],
                        self.selected_region[2] : self.selected_region[3]])
            else:
                print("Please load images.") 
                    
        
        total_magnitude_weight = sum(output_port.weight_sliders[i].value() for i in range(4) if output_port.combo_boxes[i].currentText() == "Magnitude")
        total_phase_weight = sum(output_port.weight_sliders[i].value() for i in range(4) if output_port.combo_boxes[i].currentText() == "Phase")
        total_real_weight = sum(output_port.weight_sliders[i].value() for i in range(4) if output_port.combo_boxes[i].currentText() == "Real")
        total_imaginary_weight = sum(output_port.weight_sliders[i].value() for i in range(4) if output_port.combo_boxes[i].currentText() == "Imaginary")

        if total_magnitude_weight > 0:
            magnitude_components /= total_magnitude_weight
        if total_phase_weight > 0:
            phase_components /= total_phase_weight
        if total_real_weight > 0:
            real_components /= total_real_weight
        if total_imaginary_weight > 0:
            imaginary_components /= total_imaginary_weight

        if total_real_weight > 0 or total_imaginary_weight > 0:
            reconstructed_f = real_components + 1j * imaginary_components
        else:
            reconstructed_f = magnitude_components * np.exp(1j * phase_components)
        output_port.progress_bar.setValue(50)

        reconstructed_image = np.abs(np.fft.ifft2(reconstructed_f))
        reconstructed_image = (reconstructed_image / np.max(reconstructed_image)) * 255

        reconstructed_image = np.uint8(np.clip(reconstructed_image, 0, 255))
        output_port.label.clear() 
        height, width = reconstructed_image.shape
        bytes_per_line = width
        image_bytes = reconstructed_image.tobytes()
        qimage = QImage(image_bytes, width, height, bytes_per_line, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        output_port.label.setPixmap(pixmap.scaled(output_port.label.width(), output_port.label.height(), Qt.KeepAspectRatio))
        output_port.progress_bar.setValue(100)

        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # with open("./Styling/style.css", "r") as file:
    #     app.setStyleSheet(file.read())
    
    window = ImageReconstructionApp()
    window.show()
    sys.exit(app.exec_())