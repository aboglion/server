import torch
from transformers import AutoModelForObjectDetection, AutoImageProcessor
from ultralytics import YOLO
from PIL import Image
import numpy as np
import json

# ==== קבועים לסף ====
IOU_THRESHOLD = 0.5    # סף חפיפה (למשל 0.5 = 50%)
CONFIDENCE_THRESHOLD = 0.5  # סף ממוצע אמיתות (למשל 0.5 = 50%)

def compute_iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0
    box1Area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2Area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    iou = interArea / float(box1Area + box2Area - interArea)
    return iou

def detect_persons_rtdetr(image_path, checkpoint="jadechoghari/RT-DETRv2", threshold=0.3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AutoModelForObjectDetection.from_pretrained(checkpoint).to(device)
    processor = AutoImageProcessor.from_pretrained(checkpoint)
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]])  # (height, width)
    results = processor.post_process_object_detection(
        outputs, threshold=threshold, target_sizes=target_sizes
    )[0]
    persons = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        if int(label) == 0:
            x1, y1, x2, y2 = box.tolist()
            persons.append([x1, y1, x2, y2, float(score)])
    return persons

def detect_persons_yolo(image_path, model_path="yolo11l.pt", threshold=0.3):
    model = YOLO(model_path)
    results = model(image_path)
    persons = []
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        conf = float(box.conf[0])
        if class_id == 0 and conf >= threshold:
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            persons.append([x1, y1, x2, y2, conf])
    return persons

def find_common_persons(boxes1, boxes2, iou_threshold=0.5, conf_threshold=0.5):
    matched = []
    for box1 in boxes1:
        for box2 in boxes2:
            iou = compute_iou(box1[:4], box2[:4])
            avg_conf = (box1[4] + box2[4]) / 2
            if iou >= iou_threshold and avg_conf >= conf_threshold:
                avg_box = [
                    (box1[0]+box2[0])/2,
                    (box1[1]+box2[1])/2,
                    (box1[2]+box2[2])/2,
                    (box1[3]+box2[3])/2,
                    avg_conf,
                    iou
                ]
                matched.append(avg_box)
                break
    return matched

def get_persons_bounding_box(image_path,
                             rtdetr_checkpoint="jadechoghari/RT-DETRv2",
                             yolo_model_path="yolo11l.pt",
                             iou_threshold=IOU_THRESHOLD,
                             conf_threshold=CONFIDENCE_THRESHOLD):
    persons_rtdetr = detect_persons_rtdetr(image_path, rtdetr_checkpoint)
    persons_yolo = detect_persons_yolo(image_path, yolo_model_path)
    common_persons = find_common_persons(
        persons_rtdetr, persons_yolo, iou_threshold=iou_threshold, conf_threshold=conf_threshold
    )
    if not common_persons:
        return {
            "has_person": False,
            "bounding_box": None
        }
    # מציאת הריבוע המינימלי שמכיל את כל הבני אדם
    x1s = [box[0] for box in common_persons]
    y1s = [box[1] for box in common_persons]
    x2s = [box[2] for box in common_persons]
    y2s = [box[3] for box in common_persons]
    min_x = min(x1s)
    min_y = min(y1s)
    max_x = max(x2s)
    max_y = max(y2s)
    width = max_x - min_x
    height = max_y - min_y
    return {
        "has_person": True,
        "bounding_box": {
            "X": float(min_x),
            "Y": float(min_y),
            "WIDTH": float(width),
            "HEIGHT": float(height)
        }
    }

# דוגמת שימוש: קריאה מקובץ JSON (ריקוסט)
if __name__ == "__main__":
    # קריאה מקובץ request.json

    result = get_persons_bounding_box("./3.jpg")
    # הדפסת תשובה בפורמט JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))
