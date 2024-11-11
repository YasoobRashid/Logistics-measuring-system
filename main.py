import cv2
import numpy as np
import tkinter as tk
from tkinter import simpledialog, messagebox
import datetime
import sqlite3
import paho.mqtt.client as mqtt
from camera_setup import CamRuler
from drawing_tools import DRAW
from measurement_tools import Measure
from picamera2 import Picamera2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# MQTT 
mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883
topic = "device/weight"

# Variable to store the received weight
received_weight = None

# Database setup
def setup_database():
    conn = sqlite3.connect("weights.db")
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS weight_data")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS weight_data
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user TEXT,
                       weight REAL,
                       area REAL,
                       price REAL,
                       address TEXT,
                       email TEXT,
                       phone TEXT,
                       timestamp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT,
                       phone TEXT UNIQUE,
                       email TEXT)''')
    conn.commit()
    conn.close()

# Save delivery data to the database
def save_delivery_data(user, weight, area, price, email, address, phone):
    conn = sqlite3.connect("weights.db")
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''INSERT INTO weight_data 
                      (user, weight, area, price, email, address, phone, timestamp) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                   (user, weight, area, price, email, address, phone, timestamp))
    conn.commit()
    conn.close()
    send_email(user, weight, area, price, email, address, phone, timestamp)

# Add a new user to the database
def add_user(name, phone, email):
    conn = sqlite3.connect("weights.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
        conn.commit()
        messagebox.showinfo("Success", "User added successfully!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Phone number already exists!")
    finally:
        conn.close()

# Check if a user exists
def get_user(phone):
    conn = sqlite3.connect("weights.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE phone=?", (phone,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None
    
def send_email(user, weight, area, price, email, address, phone, timestamp):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('yasoobjavaid1@gmail.com', 'tqxj dqua uoxp ynxp')

        subject = f"Delivery Confirmation for {user}"
        body = f"""
        Dear {user},

        Your shipment has been confirmed with the following details:

        - Weight: {weight} g
        - Area: {area} cm²
        - Price: ₹{price}
        - Address: {address}
        - Phone: {phone}
        - Timestamp: {timestamp}

        Thank you for choosing our service!

        Best regards,
        QuickShip Logistics
        """

        msg = MIMEMultipart()
        msg['From'] = 'yasoobjavaid1@gmail.com'
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server.sendmail('yasoobjavaid1@gmail.com', email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def on_message(client, userdata, message):
    global received_weight
    received_weight = float(message.payload.decode())
    print(f"Received weight: {received_weight} g")

def setup_mqtt_client():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(mqtt_broker, mqtt_port, 60)
    client.subscribe(topic)
    client.loop_start()  
    return client

def convert_to_srgb(image):
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    normalized_image = rgb_image.astype(np.float32) / 255.0
    srgb_image = np.where(normalized_image <= 0.0031308,
                          12.92 * normalized_image,
                          1.055 * (normalized_image ** (1 / 2.4)) - 0.055)
    srgb_image = np.clip(srgb_image * 255, 0, 255).astype(np.uint8)
    return srgb_image

def display_cost_gui(area, received_weight):
    if received_weight is None:
        messagebox.showerror("Error", "No weight data received.")
        return

    company_name = "QuickShip Logistics"
    delivery_cost = (2 * area) + (0.5 * received_weight)

    root = tk.Toplevel()
    root.title("Delivery Cost Calculation")

    tk.Label(root, text=company_name, font=("Helvetica", 16, "bold")).pack(pady=10)
    tk.Label(root, text=f"Area: {area:.2f} cmÃÂ²", font=("Helvetica", 12)).pack(pady=5)
    tk.Label(root, text=f"Weight: {received_weight:.2f} g", font=("Helvetica", 12)).pack(pady=5)
    tk.Label(root, text=f"Delivery Cost: â¹{delivery_cost:.2f}", font=("Helvetica", 12)).pack(pady=10)

    option = messagebox.askquestion("User Options", "Are you an existing user?")
    if option == 'yes':
        phone = simpledialog.askstring("Login", "Enter your phone number:")
        user = get_user(phone)
        if user:
            messagebox.showinfo("Welcome", f"Welcome back, {user}!")
            email = simpledialog.askstring("Email","Enter you email address")
            address = simpledialog.askstring("Address", "Enter the delivery address:")
            product_type = simpledialog.askstring("Product Type", "Enter the product type:")
            if address and product_type:
                save_delivery_data(user, received_weight, area, delivery_cost, email, address, phone)
                messagebox.showinfo("Data Saved", "Delivery data saved successfully!")
                # Send email to the user
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                send_email(user, received_weight, area, delivery_cost, email, address, phone, timestamp)
                
        else:
            messagebox.showerror("Error", "User not found.")
    else:
        name = simpledialog.askstring("Register", "Enter your name:")
        phone = simpledialog.askstring("Register", "Enter your phone number:")
        email= simpledialog.askstring("Register","Enter you email address:")
        if name and phone:
            add_user(name, phone, email)
            address = simpledialog.askstring("Address", "Enter the delivery address:")
            product_type = simpledialog.askstring("Product Type", "Enter the product type:")
            if address and product_type:
                save_delivery_data(name, received_weight, area, delivery_cost, email, address, phone)
                messagebox.showinfo("Data Saved", "Delivery data saved successfully!")
                # Send email to the new user
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                send_email(name, received_weight, area, delivery_cost, address, phone, timestamp)

    root.mainloop()

def open_area_input_gui():
    root = tk.Tk()
    root.withdraw()

    height = simpledialog.askfloat("Input", "Enter the height of the object (in cm):")
    width = simpledialog.askfloat("Input", "Enter the width of the object (in cm):")

    if height is not None and width is not None:
        area = height * width
        messagebox.showinfo("Area Calculation", f"The calculated area is: {area:.2f} cm^2")
        open_weight_page(area)

def open_weight_page(area):
    global received_weight
    root = tk.Tk()
    root.title("Weight Measurement")

    label = tk.Label(root, text="Waiting for weight data...", font=("Helvetica", 14))
    label.pack(pady=20)

    def check_weight():
        nonlocal label
        if received_weight is not None:
            label.config(text=f"Weight received: {received_weight:.2f} g")
            root.after(1000, lambda: root.destroy())
            display_cost_gui(area, received_weight)
        else:
            root.after(1000, check_weight)

    root.after(1000, check_weight)
    root.mainloop()

def main():
    mqtt_client = setup_mqtt_client()
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()

    measure = Measure()
    calibrated = False

    def mouse_event(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            measure.update_cursor_position((x, y))

    cv2.namedWindow("Live Measurement")
    cv2.setMouseCallback("Live Measurement", mouse_event)

    try:
        while True:
            frame = picam2.capture_array()
            frame_srgb = convert_to_srgb(frame)

            if measure.crosshair_active:
                measure.dynamic_crosshair(frame_srgb)

            if calibrated:
                contours = measure.find_contours(frame_srgb)
                measure.measure_object(frame_srgb, contours)

            cv2.imshow("Live Measurement", frame_srgb)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('c'):
                measure.calibrate(frame_srgb, known_distance_cm=10)
                calibrated = True
            elif key == ord('b'):
                measure.calibrate_with_checkerboard(frame_srgb, squares=(9, 6), square_size=1)
                calibrated = True
            elif key == ord('\r'):
                open_area_input_gui()
            elif key == ord('q'):
                break

    finally:
        picam2.stop()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    setup_database()
    main()
