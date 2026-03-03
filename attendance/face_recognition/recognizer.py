import cv2
import numpy as np
import pickle
import os
from datetime import datetime
from attendance.models import Student, Attendance

class FaceRecognizer:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Load model
        model_path = 'attendance/face_recognition/trainer/trainer.yml'
        labels_path = 'attendance/face_recognition/trainer/labels.pickle'
        
        self.student_dict = {}  # id -> student
        
        if os.path.exists(model_path) and os.path.exists(labels_path):
            self.recognizer.read(model_path)
            with open(labels_path, 'rb') as f:
                label_data = pickle.load(f)
                # Convert training_id -> student
                for train_id, student_id in label_data.items():
                    try:
                        student = Student.objects.get(id=student_id)
                        self.student_dict[train_id] = student
                        print(f"Loaded: {student.name}")
                    except:
                        pass
    
    def recognize_faces(self):
        """Simple face recognition"""
        video = cv2.VideoCapture(0)
        marked = set()
        today = datetime.now().date()
        
        print("\n📸 Camera Started - Face दाखवा")
        print("Press SPACE to mark, ESC to exit\n")
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                # Face detected - लगेच rectangle दाखवा
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "FACE DETECTED", (x, y-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Try to recognize
                if len(self.student_dict) > 0:
                    roi = gray[y:y+h, x:x+w]
                    try:
                        id_, confidence = self.recognizer.predict(roi)
                        
                        if confidence < 80:  # Recognized
                            student = self.student_dict.get(id_)
                            if student:
                                name = student.name
                                status = "RECOGNIZED"
                                color = (0, 255, 0)
                                
                                # Auto-mark if confidence is good
                                if confidence < 70 and student.id not in marked:
                                    Attendance.objects.get_or_create(
                                        student=student,
                                        date=today
                                    )
                                    marked.add(student.id)
                                    print(f"✅ Marked: {student.name}")
                            else:
                                name = "Unknown"
                                status = "UNKNOWN"
                                color = (0, 0, 255)
                        else:
                            name = "Unknown"
                            status = "LOW CONFIDENCE"
                            color = (0, 0, 255)
                        
                        # Show name and confidence
                        cv2.putText(frame, f"{name}", (x, y+h+20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        cv2.putText(frame, f"Conf: {100-confidence:.1f}%", (x, y+h+40),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    
                    except Exception as e:
                        print(f"Error: {e}")
            
            # Show info
            cv2.putText(frame, f"Marked: {len(marked)}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "SPACE: Mark | ESC: Exit", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Face Attendance', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                print(f"\n✅ Attendance saved for {len(marked)} students")
                cv2.putText(frame, "SAVED!", (200, 200),
                          cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                cv2.imshow('Face Attendance', frame)
                cv2.waitKey(1000)
                break
        
        video.release()
        cv2.destroyAllWindows()
        return marked