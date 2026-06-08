from ultralytics import YOLO

model = YOLO("models/yolov8n.pt")

# map COCO objects → factory defects (simulation layer)
DEFECT_MAP = {
    "person": "human_in_zone",
    "bottle": "foreign_object",
    "cell phone": "unauthorized_device",
    "knife": "safety_risk"
}


def detect(frame):

    results = model(frame)[0]

    defects = []

    for r in results.boxes:
        cls_id = int(r.cls[0])
        label = model.names[cls_id]

        if label in DEFECT_MAP:
            x1, y1, x2, y2 = r.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            defects.append({
                "label": DEFECT_MAP[label],
                "box": (x1, y1, x2, y2)
            })

    return defects