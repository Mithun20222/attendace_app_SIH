import streamlit as st
import os
import time
import sqlite3
import numpy as np
import cv2
from PIL import Image
import pandas as pd
import qrcode

# ---------------------- QR Code via OpenCV ----------------------
def decode_qr_opencv(img_bgr):
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img_bgr)
    if bbox is not None and data:
        return data
    return None

# ---------------------- Imports ----------------------
import db as DB
from face_recognizer import detect_faces_bgr, train_recognizer, predict_face

# ---------------------- Setup ----------------------
DB.init_db()  # creates tables if missing
os.makedirs("students", exist_ok=True)
os.makedirs("qr_codes", exist_ok=True)

st.set_page_config(page_title="School Attendance", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "home"

# Helpers
def goto_attendance(class_name, section, date_str):
    st.session_state.page = "attendance"
    st.session_state.selected_class = class_name
    st.session_state.selected_section = section
    st.session_state.selected_date = date_str

def go_home():
    st.session_state.page = "home"

# ---------------------- Home Page ----------------------
if st.session_state.page == "home":
    st.title("📚 School Attendance System")

    class_selected = st.selectbox("Select Class", [str(i) for i in range(1, 11)])
    section_selected = st.selectbox("Select Section", ["A", "B", "C", "D"])
    date_selected = st.date_input("Select Date")

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("➡️ Go to Attendance Page"):
            goto_attendance(class_selected, section_selected, str(date_selected))
            st.rerun()

    with c2:
        st.subheader("📊 Monthly Report")
        month_for = st.text_input("Enter month as YYYY-MM (e.g. 2025-09)", value=time.strftime("%Y-%m"))
        if st.button("Get Monthly Report"):
            rows = DB.get_monthly_report(class_selected, section_selected, month_for)
            if rows:
                df = pd.DataFrame(rows, columns=["id","name","presents","total_marked"])
                st.dataframe(df)
                st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                                   f"{class_selected}_{section_selected}_{month_for}.csv")
            else:
                st.info("No records found for that month / class-section.")

    st.write("---")
    st.write("💡 Tip: Add students first (Add Student option in Attendance page).")

# ---------------------- Attendance Page ----------------------
elif st.session_state.page == "attendance":
    st.title("📸 Attendance Page")
    cls = st.session_state.get("selected_class")
    sec = st.session_state.get("selected_section")
    date_sel = st.session_state.get("selected_date")

    if not (cls and sec and date_sel):
        st.warning("Missing class/section/date. Returning to Home.")
        if st.button("⬅️ Back"):
            go_home()
            st.rerun()
        st.stop()

    st.subheader(f"Class: {cls}  |  Section: {sec}  |  Date: {date_sel}")

    option = st.radio("Choose an option:",
                      ["📷 Take Attendance", "✏️ Edit Attendance (QR)", "📝 Day Report", "➕ Add Student"])

    # Show students helper
    def show_students_list():
        rows = DB.get_students(cls, sec)
        if not rows:
            st.info("No students found for this class/section. Please add students.")
        else:
            st.write("👩‍🎓 Students in this section:")
            for sid, name, _ in rows:
                st.write(f"{sid} - {name}")

    # ---------------- Take Attendance ----------------
    if option == "📷 Take Attendance":
        st.header("Take Attendance — Capture or Upload group photo")

        col1, col2 = st.columns(2)
        with col1:
            photo = st.camera_input("Take class photo with camera")
        with col2:
            photo2 = st.file_uploader("Or upload class photo", type=["jpg","jpeg","png"])
            if photo2 and not photo:
                photo = photo2

        if photo:
            img_bytes = photo.read()
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
                     caption="Class photo", use_container_width=True)

            with st.spinner("Detecting faces..."):
                faces = detect_faces_bgr(img)
            st.write(f"Detected {len(faces)} faces.")

            ok, msg = train_recognizer()
            if not ok:
                st.warning("Recognizer not trained - no students in DB. Add students first.")
            else:
                present = []
                recognized_ids = set()
                unknown = []

                for i, (face_img, bbox) in enumerate(faces):
                    student_id, conf = predict_face(face_img)
                    if student_id:
                        DB.mark_attendance(student_id, date_sel, "Present")
                        info = DB.get_student_by_id(student_id)
                        present.append((student_id, info[1], conf))
                        recognized_ids.add(student_id)
                    else:
                        unknown.append((i+1, conf))

                # Mark all other students as Absent
                all_students = DB.get_students(cls, sec)
                for sid, name, _ in all_students:
                    if sid not in recognized_ids:
                        DB.mark_attendance(sid, date_sel, "Absent")

                st.success("Attendance updated ✅")

                if present:
                    st.write("✅ Recognized / Present:")
                    for sid, name, conf in present:
                        st.write(f"{sid} - {name}  (conf={conf:.1f})")

                if unknown:
                    st.warning("⚠️ Unrecognized faces (use QR/manual correction):")
                    for idx, conf in unknown:
                        st.write(f"Face #{idx}  (confidence={conf:.1f})")

                total_students = len(all_students)
                st.info(f"Summary for {date_sel}: {len(present)} Present, {total_students - len(present)} Absent, Total {total_students}")

    # ---------------- Edit Attendance via QR ----------------
    elif option == "✏️ Edit Attendance (QR)":
        st.header("Edit Attendance — QR")

        col1, col2 = st.columns(2)
        with col1:
            qr_cam = st.camera_input("Scan QR code with camera")
        with col2:
            qr_file = st.file_uploader("Or upload QR code image", type=["png","jpg","jpeg"])

        qr_img = None
        if qr_cam:
            qr_img = qr_cam
        elif qr_file:
            qr_img = qr_file

        manual_id = st.text_input("Or enter Student ID manually")

        if st.button("Apply QR / Mark Present"):
            found_id = None
            if qr_img is not None:
                img_bytes = qr_img.read()
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                data = decode_qr_opencv(img)
                if data:
                    try:
                        found_id = int(data)
                    except:
                        st.error("QR decoded but not a valid student ID.")
                else:
                    st.error("No QR code detected. Try again or enter ID manually.")

            if manual_id:
                try:
                    found_id = int(manual_id.strip())
                except:
                    st.error("Manual ID must be integer.")

            if found_id:
                student = DB.get_student_by_id(found_id)
                if student:
                    DB.mark_attendance(found_id, date_sel, "Present")
                    st.success(f"{student[1]} marked Present for {date_sel}")
                else:
                    st.error("Student ID not found in DB.")

    # ---------------- Day Report ----------------
    elif option == "📝 Day Report":
        st.header(f"Attendance report for {date_sel}")
        rows = DB.get_attendance_report(cls, sec, date_sel)
        if rows:
            df = pd.DataFrame(rows, columns=["id","name","status"])
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'),
                               f"{cls}_{sec}_{date_sel}.csv")
        else:
            st.info("No students / records for this class on this date.")

    # ---------------- Add Student ----------------
    elif option == "➕ Add Student":
        st.header("Add new student to this class/section")
        name = st.text_input("Student Name")

        col1, col2 = st.columns(2)
        with col1:
            cam_photo = st.camera_input("Take student photo with camera")
        with col2:
            uploaded = st.file_uploader("Or upload student photo (frontal)", type=["jpg","jpeg","png"])

        photo_file = None
        if cam_photo:
            photo_file = cam_photo
        elif uploaded:
            photo_file = uploaded

        if st.button("Add Student"):
            if not name or not photo_file:
                st.error("Provide name and photo.")
            else:
                fname = f"students/{int(time.time())}_{name.replace(' ','_')}.jpg"
                with open(fname, "wb") as f:
                    f.write(photo_file.read())

                sid = DB.add_student(name, cls, sec, fname, None)

                qr_img = qrcode.make(str(sid))
                qr_path = f"qr_codes/{sid}.png"
                qr_img.save(qr_path)

                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                c.execute("UPDATE students SET qr_path=? WHERE id=?", (qr_path, sid))
                conn.commit()
                conn.close()

                ok, msg = train_recognizer()
                st.success(f"Student {name} added with ID {sid}")
                st.image(qr_path, caption="QR Code (scan or download)")
                with open(qr_path, "rb") as f:
                    st.download_button("Download QR (PNG)", f.read(),
                                       file_name=f"{sid}.png", mime="image/png")

    st.write("---")
    if st.button("⬅️ Back to Home"):
        go_home()
        st.rerun()

    st.button("Show students in this class", on_click=show_students_list)
