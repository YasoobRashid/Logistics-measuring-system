from picamera2 import Picamera2
import cv2
import numpy as np

class CamRuler:
    def __init__(self, resolution=(640, 480)):
        self.picam2 = Picamera2()
        self.resolution = resolution
        self.configure_camera()
        self.distortion_coefficients = None  # Store calibration results
        self.camera_matrix = None

    def configure_camera(self):
        config = self.picam2.create_preview_configuration(main={"size": self.resolution})
        self.picam2.configure(config)
        self.picam2.start()

    def display_checkerboard(self, squares=(9, 6), square_size=1):
        """
        Generate and display a virtual checkerboard for calibration.
        """
        board_image = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        checker_size = int(min(self.resolution) / max(squares))

        for i in range(squares[1]):
            for j in range(squares[0]):
                if (i + j) % 2 == 0:
                    top_left = (j * checker_size, i * checker_size)
                    bottom_right = ((j + 1) * checker_size, (i + 1) * checker_size)
                    cv2.rectangle(board_image, top_left, bottom_right, (255, 255, 255), -1)

        cv2.imshow("Checkerboard Calibration", board_image)
        cv2.waitKey(0)
        cv2.destroyWindow("Checkerboard Calibration")

    def get_frame(self):
        # Capture a frame from the camera, and apply distortion correction if calibrated
        frame = self.picam2.capture_array()
        if self.camera_matrix is not None:
            frame = cv2.undistort(frame, self.camera_matrix, self.distortion_coefficients)
        return frame

    def stop(self):
        self.picam2.stop()
