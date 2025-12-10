import cv2
from ultralytics import YOLO
from utils import draw_box, timestamp

# Path model
MODEL_PATH = "../models/yolo_vehicle.pt"  # update sesuai path

# Area slots (manual) -> list of bounding boxes (x1,y1,x2,y2)
# Kamu bisa mendefinisikan slot secara manual per camera
SLOTS = [
    (50,200,220,420),
    (240,200,410,420),
    # tambah sesuai layout parkir
]

def is_slot_occupied(slot_bbox, detections, iou_thresh=0.1):
    x1,y1,x2,y2 = slot_bbox
    for det in detections:
        bx1,by1,bx2,by2 = det
        # intersection area
        ix1 = max(x1,bx1); iy1 = max(y1,by1)
        ix2 = min(x2,bx2); iy2 = min(y2,by2)
        if ix2>ix1 and iy2>iy1:
            inter = (ix2-ix1)*(iy2-iy1)
            slot_area = (x2-x1)*(y2-y1)
            if inter/slot_area > iou_thresh:
                return True
    return False

def main(video_path=0):
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap.read()
        if not ret: break
        results = model(frame, imgsz=640)[0]
        dets = []
        for r in results.boxes:
            x1,y1,x2,y2 = map(int, r.xyxy[0])
            conf = float(r.conf[0])
            # optionally filter by conf
            if conf < 0.3: continue
            dets.append((x1,y1,x2,y2))
            draw_box(frame, (x1,y1,x2,y2), label=f'car {conf:.2f}')
        # check slots
        occupied = 0
        for i,slot in enumerate(SLOTS):
            occ = is_slot_occupied(slot, dets)
            color = (0,0,255) if occ else (0,255,0)
            draw_box(frame, slot, label=f'slot {i+1}', color=color)
            if occ: occupied += 1
        cv2.putText(frame, f'Occupied: {occupied}/{len(SLOTS)}', (20,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255),2)
        cv2.imshow('Parking', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main(0)
