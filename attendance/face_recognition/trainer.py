import cv2
import numpy as np
import os
import pickle

def train_face_model():
    """Train face recognition model"""
    
    # Create directories if not exist
    trainer_dir = 'attendance/face_recognition/trainer'
    if not os.path.exists(trainer_dir):
        os.makedirs(trainer_dir)
    
    # Initialize face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    # Initialize LBPH recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    face_samples = []
    ids = []
    id_counter = 0
    id_mapping = {}  # student.id -> training_id
    
    # Get all student images
    from attendance.models import Student
    students = Student.objects.exclude(face_image='')
    
    print(f"\nFound {students.count()} students with images")
    
    for student in students:
        if student.face_image and os.path.exists(student.face_image.path):
            # Read image
            img = cv2.imread(student.face_image.path)
            if img is None:
                print(f"Error reading image for {student.name}")
                continue
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect face
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                print(f"No face detected in image for {student.name}")
                continue
            
            for (x, y, w, h) in faces:
                face_samples.append(gray[y:y+h, x:x+w])
                id_mapping[id_counter] = student.id
                ids.append(id_counter)
                id_counter += 1
                print(f"✓ Added face for student: {student.name} (ID: {student.id})")
    
    if len(face_samples) > 0:
        # Train recognizer
        recognizer.train(face_samples, np.array(ids))
        
        # Save model
        model_path = os.path.join(trainer_dir, 'trainer.yml')
        recognizer.save(model_path)
        
        # Save labels mapping
        labels_path = os.path.join(trainer_dir, 'labels.pickle')
        with open(labels_path, 'wb') as f:
            pickle.dump(id_mapping, f)
        
        print(f"\n✓ Training complete! {len(face_samples)} faces trained")
        print(f"Model saved to: {model_path}")
        print(f"Labels saved to: {labels_path}")
        return True
    else:
        print("\n✗ No faces found to train")
        return False