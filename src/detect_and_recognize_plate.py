import cv2
from ultralytics import YOLO
import easyocr
from utils import draw_box, timestamp

PLATE_MODEL = "../models/yolo_plate.pt"

def main(video_path=0):
    plate_model = YOLO(PLATE_MODEL)
    reader = easyocr.Reader(['en'])  # tambahin bahasa sesuai region (mis. 'id' jika tersedia)
    cap = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap.read()
        if not ret: break
        results = plate_model(frame, imgsz=640)[0]
        for r in results.boxes:
            x1,y1,x2,y2 = map(int, r.xyxy[0])
            plate_crop = frame[y1:y2, x1:x2]
            if plate_crop.size == 0: continue
            # preprocess for OCR
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
            # optional thresh
            # _,th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # use EasyOCR
            res = reader.readtext(gray)
            text = ""
            if res:
                # take highest confidence
                res = sorted(res, key=lambda x: x[2], reverse=True)
                text = res[0][1]
            draw_box(frame, (x1,y1,x2,y2), label=text)
            # log
            print(f"{timestamp()} | Plate: {text} | bbox: {(x1,y1,x2,y2)}")
        cv2.imshow('Plate OCR', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main(0)
