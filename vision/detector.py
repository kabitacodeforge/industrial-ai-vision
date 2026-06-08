
from ultralytics import YOLO

model = YOLO("models/yolov8n.pt")

def detect(frame):
	results = model(frame)

	defects = []

	for r in results:
		for box in r.boxes:
			label = model.names[int(box.cls[0])]

			if label in ["crack", "damage", "missing_part"]:
				defects.append(label)

	return defects
