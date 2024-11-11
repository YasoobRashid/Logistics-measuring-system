import cv2  # OpenCV for image processing
import numpy as np  # NumPy for array manipulations

class Measure:
    def __init__(self):
        self.pixel_to_cm_ratio = None  # Will be set after calibration
        self.crosshair_active = True  # Crosshair follows the mouse initially
        self.ref_points = []  # To store the calibration points
        self.cursor_pos = (0, 0)  # Position of the cursor for crosshair
        self.distortion_coefficients = None
        self.camera_matrix = None

    def dynamic_crosshair(self, frame):
        """
        Draw dynamic crosshairs that follow the mouse cursor.
        """
        x, y = self.cursor_pos
        color = (0, 255, 0)
        thickness = 1
        width, height = frame.shape[1], frame.shape[0]

        # Draw center crosshairs
        cv2.line(frame, (x, 0), (x, height), color, thickness)
        cv2.line(frame, (0, y), (width, y), color, thickness)

        # Draw diagonal crosshairs
        cv2.line(frame, (x - 50, y - 50), (x + 50, y + 50), color, thickness)
        cv2.line(frame, (x - 50, y + 50), (x + 50, y - 50), color, thickness)

        # Display pixel coordinates at the cursor location
        cv2.putText(frame, f"({x}, {y})", (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def fixed_crosshairs(self, frame, center_x, center_y):
        """
        Draw fixed crosshairs at the center with diagonal lines.
        """
        color = (255, 0, 0)
        thickness = 1
        width, height = frame.shape[1], frame.shape[0]

        # Draw crosshairs at the center
        cv2.line(frame, (center_x, 0), (center_x, height), color, thickness)
        cv2.line(frame, (0, center_y), (width, center_y), color, thickness)

        # Draw diagonal crosshairs
        cv2.line(frame, (center_x - 50, center_y - 50), (center_x + 50, center_y + 50), color, thickness)
        cv2.line(frame, (center_x - 50, center_y + 50), (center_x + 50, center_y - 50), color, thickness)

    def calibrate_with_checkerboard(self, frame, squares=(7, 5), square_size=1):
        """
        Calibrate using a virtual checkerboard pattern by detecting corners.
        """
        objp = np.zeros((squares[0] * squares[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:squares[0], 0:squares[1]].T.reshape(-1, 2) * square_size
        objpoints = []
        imgpoints = []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, squares, None)

        if ret:
            # Draw the detected corners on the frame for visualization
            cv2.drawChessboardCorners(frame, squares, corners, ret)
            cv2.imshow("Checkerboard Detection", frame)
            cv2.waitKey(1)

            objpoints.append(objp)
            imgpoints.append(corners)

            ret, camera_matrix, dist_coeffs, _, _ = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

            if ret:
                self.camera_matrix = camera_matrix
                self.distortion_coefficients = dist_coeffs
                print("Calibration successful.")
            else:
                print("Calibration failed.")
        else:
            print("Checkerboard pattern not detected. Ensure the pattern is clearly visible in the frame.")

        cv2.destroyWindow("Checkerboard Detection")

    def calibrate(self, frame, known_distance_cm):
        """
        Calibrate the system by allowing the user to measure a known distance (in cm)
        using mouse clicks or crosshair points.
        """
        print("Calibration mode: Please click two points to measure a known distance.")
        clone = frame.copy()
        self.ref_points = []  # Reset reference points for calibration

        def click_event(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.ref_points.append((x, y))
                # Draw a small circle where the user clicked
                cv2.circle(clone, (x, y), 5, (0, 255, 0), -1)
                if len(self.ref_points) == 2:
                    # Draw a line between the two points
                    cv2.line(clone, self.ref_points[0], self.ref_points[1], (255, 0, 0), 2)
                    cv2.imshow("Calibration", clone)

        # Set mouse callback to detect clicks and draw dynamic crosshair
        cv2.imshow("Calibration", clone)
        cv2.setMouseCallback("Calibration", click_event)

        while len(self.ref_points) < 2:
            # Capture the live frame and update crosshair based on mouse position
            frame = cv2.flip(frame, 1)
            self.dynamic_crosshair(clone)
            cv2.imshow("Calibration", clone)
            cv2.waitKey(1)

        # Calculate the pixel distance between the two points
        (x1, y1), (x2, y2) = self.ref_points
        pixel_distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        # Calculate the pixel-to-centimeter ratio
        self.pixel_to_cm_ratio = known_distance_cm / pixel_distance
        print(f"Calibration complete. Pixel-to-CM ratio: {self.pixel_to_cm_ratio:.4f} cm/pixel")

        cv2.destroyWindow("Calibration")
        self.crosshair_active = False  # Stop dynamic crosshairs after calibration

    def find_contours(self, frame):
        """
        Find contours in the frame for object measurement.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(blurred, 50, 100)
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def measure_object(self, frame, contours):
        """
        Measure objects using contours found in the frame.
        """
        if self.pixel_to_cm_ratio is None:
            raise ValueError("System is not calibrated. Please calibrate first.")

        for c in contours:
            if cv2.contourArea(c) > 1000:  # Filter out small objects
                # Get the bounding box of the contour
                x, y, w, h = cv2.boundingRect(c)

                # Draw the bounding box and show dimensions in cm
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                self.draw_dimensions(frame, x, y, w, h)

    def draw_dimensions(self, frame, x, y, w, h):
        """
        Draw the width and height in centimeters on the frame.
        """
        # Convert pixels to cm using the pixel-to-cm ratio
        width_in_cm = w * self.pixel_to_cm_ratio
        height_in_cm = h * self.pixel_to_cm_ratio

        # Display width and height in cm on the frame
        cv2.putText(frame, f"W: {width_in_cm:.2f} cm", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.putText(frame, f"H: {height_in_cm:.2f} cm", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    def update_cursor_position(self, pos):
        """
        Update the cursor position for dynamic crosshair.
        """
        self.cursor_pos = pos
