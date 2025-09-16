📚 Face Recognition Attendance System

This is a Streamlit-based Attendance Management System that uses face detection and recognition to automatically mark students Present/Absent.
Teachers can also edit attendance via QR codes, add students with photos, and download daily/monthly reports.

🚀 Features

Class & Section Selection → choose class, section, and date.

Face Detection → powered by MediaPipe.

Face Recognition → powered by OpenCV LBPHFaceRecognizer.

Automatic Attendance → recognized students = Present, others = Absent.

QR Fallback → scan or upload QR code to fix misdetections.

Add Students → capture photo from webcam OR upload, generates QR code.

Daily Report → shows attendance for the selected day.

Monthly Report → shows total presents, absents, and attendance percentage.

CSV Export → download reports for record keeping.

🛠️ Tech Stack

Frontend → Streamlit

Face Detection → MediaPipe Face Detection

Face Recognition → OpenCV LBPH

Database → SQLite (database.db)

QR Codes → OpenCV QRCodeDetector (decode) + qrcode (generate)

📂 Project Structure
attendance_app/
│
├── app.py                # Main Streamlit app
├── db.py                 # Database functions
├── face_recognizer.py    # Face detection & recognition logic
├── database.db           # SQLite DB (auto-created)
├── students/             # Stored student photos
├── qr_codes/             # Generated QR codes
├── recognizer.yml        # Trained LBPH face recognizer model
└── requirements.txt      # Python dependencies

⚡ Installation & Setup

Clone repo

git clone https://github.com/yourusername/attendance_app.git
cd attendance_app


Create a virtual environment

python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows


Install dependencies

pip install -r requirements.txt


Run app

streamlit run app.py

📦 Requirements

requirements.txt should contain:

streamlit
opencv-contrib-python
mediapipe
pillow
qrcode
pandas

📊 Usage Flow

Select Class/Section/Date → on Home Page.

Add Students → capture or upload a photo, QR code is generated.

Take Attendance → capture/upload class photo, faces recognized as Present, others marked Absent.

Edit Attendance → scan/upload QR code to fix mistakes.

View Reports → Daily report (per day) or Monthly report (summary).

🗂️ Data Storage

Students → stored in database.db + photo in students/ + QR in qr_codes/.

Attendance → stored in database.db (attendance table).

Recognizer Model → recognizer.yml (auto-generated, can be rebuilt).

🙌 Future Improvements

Add teacher login/authentication.

Improve accuracy with deep-learning models (face_recognition, FaceNet).

Cloud DB + report syncing for multi-device use.

Mobile-first UI improvements.

📜 License

This project is for educational/demo purposes.
Feel free to fork & adapt for your school/college.
