# ui/app.py
import streamlit as st
import cv2
import tempfile
import time
import os
import sqlite3
from datetime import datetime
from ultralytics import YOLO
import easyocr
import numpy as np
import pandas as pd
from src.occupancy_manager import OccupancyManager  # ensure this is the parking version

# -----------------------
# Config / Globals
# -----------------------
MODEL_PLATE = os.path.join("..", "models", "yolo_plate.pt")
MODEL_VEH = os.path.join("..", "models", "yolo_vehicle.pt")
DB_PATH = os.path.join("..", "data", "parking.db")
DEFAULT_RATE_PER_HOUR = 2000.0  # e.g., Rp 2000 per hour

st.set_page_config(page_title="Smart Parking AI", layout="wide", page_icon="🅿️")

# -----------------------
# Helpers: DB
# -----------------------
def init_db(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS parking_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT,
        entry_time TEXT,
        exit_time TEXT,
        paid INTEGER DEFAULT 0,
        fee REAL DEFAULT 0
    );
    """)
    conn.commit()
    return conn

def add_entry(conn, plate):
    cur = conn.cursor()
    # if there's an open entry (exit_time IS NULL) for this plate, ignore
    cur.execute("SELECT id FROM parking_log WHERE plate=? AND exit_time IS NULL", (plate,))
    if cur.fetchone():
        return False
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    cur.execute("INSERT INTO parking_log (plate, entry_time) VALUES (?, ?)", (plate, now))
    conn.commit()
    return True

def close_entry(conn, plate, rate_per_hour):
    cur = conn.cursor()
    cur.execute("SELECT id, entry_time FROM parking_log WHERE plate=? AND exit_time IS NULL ORDER BY id DESC LIMIT 1", (plate,))
    row = cur.fetchone()
    if not row:
        return False
    rec_id, entry_time = row
    entry_dt = datetime.fromisoformat(entry_time)
    exit_dt = datetime.now()
    duration = (exit_dt - entry_dt).total_seconds() / 3600.0  # hours
    fee = max(0.0, duration * rate_per_hour)
    cur.execute("UPDATE parking_log SET exit_time=?, fee=? WHERE id=?", (exit_dt.isoformat(sep=' ', timespec='seconds'), round(fee,2), rec_id))
    conn.commit()
    return True

def list_open_entries(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, plate, entry_time FROM parking_log WHERE exit_time IS NULL ORDER BY entry_time DESC")
    rows = cur.fetchall()
    return rows

def get_history(conn, limit=200):
    cur = conn.cursor()
    cur.execute("SELECT id, plate, entry_time, exit_time, fee, paid FROM parking_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["id","plate","entry_time","exit_time","fee","paid"])
    return df

def mark_paid(conn, rec_id):
    cur = conn.cursor()
    cur.execute("UPDATE parking_log SET paid=1 WHERE id=?", (rec_id,))
    conn.commit()

# -----------------------
# Helpers: Models + OCR
# -----------------------
@st.cache_resource(show_spinner=False)
def load_models(plate_model_path=MODEL_PLATE, veh_model_path=MODEL_VEH):
    plate_model = YOLO(plate_model_path)
    # vehicle model optional; used to estimate occupancy by counting vehicles
    veh_model = None
    if os.path.exists(veh_model_path):
        try:
            veh_model = YOLO(veh_model_path)
        except Exception:
            veh_model = None
    reader = easyocr.Reader(['en'], gpu=False)  # set gpu=True if you have CUDA and torch with GPU
    return plate_model, veh_model, reader

def clean_plate_text(text):
    # uppercase, remove weird chars, keep alnum + dash/space
    if not text: 
        return ""
    cleaned = "".join(ch for ch in text.upper() if (ch.isalnum() or ch in ("-", " ")))
    cleaned = cleaned.strip()
    return cleaned

# -----------------------
# UI Layout
# -----------------------
st.title("🅿️ Smart Parking — LPR + Occupancy + Billing")
left, mid, right = st.columns([1,2,1])

# LEFT: Settings & Controls
with left:
    st.header("Settings")
    total_slots = st.number_input("Total parking slots", value=20, min_value=1, step=1)
    rate_per_hour = st.number_input("Rate (per hour)", value=float(DEFAULT_RATE_PER_HOUR), step=500.0)
    realtime_checkbox = st.checkbox("Use webcam (realtime)", value=False)
    uploaded_file = st.file_uploader("Or upload video (mp4/avi)", type=["mp4","avi","mov"])
    st.markdown("---")
    st.write("DB path:", DB_PATH)
    if st.button("Initialize DB"):
        conn = init_db()
        st.success("DB initialized at: " + DB_PATH)

# MID: Video + Detection Stream
with mid:
    st.header("Live View / Video Analysis")
    plate_model, veh_model, reader = load_models()
    conn = init_db()

    # placeholders
    video_placeholder = st.empty()
    stats_placeholder = st.empty()
    plate_list_placeholder = st.empty()

    # occupancy manager
    occ = OccupancyManager(total_slots)

    def process_frame(frame):
        # detect plates
        results = plate_model(frame, imgsz=640)
        ann = results[0].plot()  # annotated frame (BGR)
        plates = []
        for box in results[0].boxes:
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0: 
                continue
            # preprocess crop for OCR
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            # resize small plates to help OCR
            h, w = gray.shape[:2]
            if w < 100:
                scale = int(100 / max(w,1))
                gray = cv2.resize(gray, (w*scale, h*scale), interpolation=cv2.INTER_CUBIC)
            try:
                ocr_res = reader.readtext(gray)
            except Exception:
                ocr_res = []
            text = ""
            if ocr_res:
                # choose highest confidence
                ocr_res = sorted(ocr_res, key=lambda x: x[2], reverse=True)
                text = ocr_res[0][1]
            text = clean_plate_text(text)
            plates.append((text, (x1,y1,x2,y2)))
            # draw label
            cv2.putText(ann, text, (x1, y1-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        return ann, plates

    # choose source
    stop_signal = False
    if realtime_checkbox:
        cap = cv2.VideoCapture(0)
    elif uploaded_file:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp.write(uploaded_file.read())
        tmp.flush()
        cap = cv2.VideoCapture(tmp.name)
    else:
        cap = None

    if cap is not None:
        stframe = st.image(np.zeros((480,640,3), dtype=np.uint8), channels="BGR")
        run_btn = st.button("Start Processing")
        stop_btn = st.button("Stop")
        processing = False
        if run_btn:
            processing = True
            last_seen = {}
            cooldown_seconds = 6  # avoid duplicate rapid-fire detections
            while processing and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.resize(frame, (960, int(frame.shape[0] * 960 / frame.shape[1]))) if frame.shape[1] > 960 else frame
                annotated, plates = process_frame(frame)

                # handle each plate: add entry / close entry if seen earlier
                now_s = time.time()
                for text, bbox in plates:
                    if not text:
                        continue
                    # simple de-dup by text + cooldown
                    last_time = last_seen.get(text, 0)
                    if now_s - last_time < cooldown_seconds:
                        continue
                    last_seen[text] = now_s

                    # If there's an open entry for this plate -> close it (exit)
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM parking_log WHERE plate=? AND exit_time IS NULL", (text,))
                    open_row = cur.fetchone()
                    if open_row:
                        closed = close_entry(conn, text, rate_per_hour)
                        if closed:
                            st.info(f"Exit recorded: {text}")
                            occ.vehicle_exit(1)
                    else:
                        added = add_entry(conn, text)
                        if added:
                            st.success(f"Entry recorded: {text}")
                            occ.vehicle_enter(1)

                stframe.image(annotated, channels="BGR")
                stats_placeholder.markdown(f"**Occupancy:** {occ.occupied_slots}/{occ.total_slots} • **Free:** {occ.free_slots()} • Rate: Rp{rate_per_hour}/hr")
                plate_list_placeholder.write(pd.DataFrame([{"plate":p[0], "bbox":p[1]} for p in plates]))
                # check stop btn
                if st.button("Stop Processing"):
                    break
                # small sleep so Streamlit UI stays responsive
                time.sleep(0.05)
        cap.release()
    else:
        st.info("No source selected. Toggle webcam or upload video to start.")

# RIGHT: Management Panel & History
with right:
    st.header("Management")
    conn = init_db()
    st.subheader("Open Entries (currently parked)")
    open_rows = list_open_entries(conn)
    if open_rows:
        for rec in open_rows:
            rec_id, plate, entry_time = rec
            st.write(f"• Plate: **{plate}** — Entry: {entry_time}")
            cols = st.columns([1,1,1])
            if cols[0].button(f"Close (exit) {rec_id}", key=f"close_{rec_id}"):
                close_entry(conn, plate, rate_per_hour)
                st.experimental_rerun()
            if cols[1].button(f"Mark Paid {rec_id}", key=f"paid_{rec_id}"):
                mark_paid(conn, rec_id)
                st.experimental_rerun()
    else:
        st.write("No vehicles currently parked.")

    st.markdown("---")
    st.subheader("History")
    history_df = get_history(conn)
    st.dataframe(history_df)
    if st.button("Export CSV"):
        tmp_path = os.path.join(tempfile.gettempdir(), "parking_history.csv")
        history_df.to_csv(tmp_path, index=False)
        with open(tmp_path, "rb") as f:
            st.download_button("Download history.csv", f, file_name="parking_history.csv")

st.markdown("---")
st.caption("Notes: OCR can misread plates; adjust rate and cooldown as needed. Use better model if needed for local plates.")
