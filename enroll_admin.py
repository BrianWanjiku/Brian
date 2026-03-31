import cv2
import face_recognition
import sqlite3
import sys
from datetime import datetime

def enroll():
    print(" [Sovereign] Initializing Biometric Enrollment...")
    video_capture = cv2.VideoCapture(0)
    
    print(" Please look directly at the camera. Capturing in 3...")
    for i in range(2, 0, -1):
        cv2.waitKey(1000)
        print(f" {i}...")

    ret, frame = video_capture.read()
    video_capture.release()

    if not ret:
        print(" ❌ Error: Could not access camera.")
        return

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_frame)

    if len(encodings) == 0:
        print(" ❌ Error: No face detected. Please try again in better lighting.")
        return

    admin_encoding = encodings[0].tobytes() # Convert numpy array to blob

    try:
        conn = sqlite3.connect('database/security.db')
        cur = conn.cursor()
        
        # Insert Admin
        cur.execute(
            "INSERT INTO security_registry (name, encoding, clearance, scope) VALUES (?, ?, ?, ?)",
            ("Admin", admin_encoding, "LEVEL_5", "GLOBAL")
        )
        
        # Log the event
        cur.execute(
            "INSERT INTO audit_log (timestamp, event, detail) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), "ADMIN_ENROLLED", "Primary biometric signature captured.")
        )
        
        conn.commit()
        conn.close()
        print(" ✅ Admin Biometrics successfully locked to security.db")
    except Exception as e:
        print(f" ❌ Database Error: {e}")

if __name__ == "__main__":
    enroll()
