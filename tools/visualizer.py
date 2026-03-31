# jarvis/tools/visualizer.py
import cv2

def draw_machine_ui(frame, faces, status):
    """
    Overlays a Finch-style UI on top of the raw camera frame.
    Draws the Admin bounding box in Yellow, unauthorized in Red.
    Draws the 2D facial landmark mesh.
    """
    for face in faces:
        bbox = face.bbox.astype(int)
        color = (0, 255, 255) if status == "ADMIN" else (0, 0, 255) # Yellow vs Red
        
        # Draw the 'Sovereign' bounding box
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
        
        # Draw the Face Mesh (Landmarks)
        if hasattr(face, 'landmark_2d') and face.landmark_2d is not None:
            for pt in face.landmark_2d.astype(int):
                cv2.circle(frame, tuple(pt), 1, (0, 255, 0), -1)
            
    cv2.putText(frame, f"SYSTEM: {status}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return frame
