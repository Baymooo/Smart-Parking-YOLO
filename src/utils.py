import cv2
import numpy as np
from datetime import datetime

def draw_box(img, bbox, label=None, color=(0,255,0), thickness=2):
    x1,y1,x2,y2 = bbox
    cv2.rectangle(img, (x1,y1), (x2,y2), color, thickness)
    if label:
        cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return img

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")