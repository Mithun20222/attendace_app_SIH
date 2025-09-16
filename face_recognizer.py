# face_recognizer.py
import cv2
import mediapipe as mp
import numpy as np
import os
from db import get_students

RECOGNIZER_PATH = "recognizer.yml"
mp_face = mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5)

def detect_faces_bgr(img_bgr):
    """Return list of (face_bgr, bbox) where bbox=(x1,y1,x2,y2)"""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = mp_face.process(img_rgb)
    h, w = img_bgr.shape[:2]
    faces = []
    if results.detections:
        for det in results.detections:
            bbox = det.location_data.relative_bounding_box
            x1 = int(bbox.xmin * w)
            y1 = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)
            x1 = max(0, x1); y1 = max(0, y1)
            x2 = min(w, x1 + bw); y2 = min(h, y1 + bh)
            face = img_bgr[y1:y2, x1:x2]
            faces.append((face, (x1, y1, x2, y2)))
    return faces

def train_recognizer(image_size=(200,200)):
    students = get_students()
    images = []
    labels = []
    for sid, name, img_path in students:
        if not os.path.exists(img_path):
            continue
        img = cv2.imread(img_path)
        faces = detect_faces_bgr(img)
        if faces:
            face_crop = faces[0][0]
        else:
            face_crop = img
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, image_size)
        images.append(gray)
        labels.append(int(sid))
    if len(images) == 0:
        return False, "No training images"
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, np.array(labels))
    recognizer.write(RECOGNIZER_PATH)
    return True, f"Trained on {len(images)} images"

def predict_face(face_bgr, image_size=(200,200), threshold=70):
    """Return (student_id, confidence) or (None, None) if unknown"""
    if not os.path.exists(RECOGNIZER_PATH):
        return None, None
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(RECOGNIZER_PATH)
    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, image_size)
    label, conf = recognizer.predict(gray)  # label = student_id
    # LBPH: smaller conf = better match. threshold tuneable.
    if conf <= threshold:
        return int(label), conf
    else:
        return None, conf
