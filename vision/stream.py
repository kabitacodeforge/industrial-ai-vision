import cv2
from vision.yolo_engine import detect


def get_color(severity):
    if severity == "HIGH":
        return (0, 0, 255)      # red
    elif severity == "MEDIUM":
        return (0, 255, 255)    # yellow
    else:
        return (0, 255, 0)      # green


def generate_frames():
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        defects = detect(frame)

        severity = "LOW"
        alert_text = "NORMAL OPERATION"

        # ---------------- DRAW DEFECTS ----------------
        for d in defects:
            label = d["label"]
            x1, y1, x2, y2 = d["box"]

            severity = "MEDIUM"

            if label in ["human_in_zone", "safety_risk"]:
                severity = "HIGH"

            color = get_color(severity)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # ---------------- GLOBAL ALERT ----------------
        if severity == "HIGH":
            alert_text = "⚠ CRITICAL ALERT"
        elif severity == "MEDIUM":
            alert_text = "⚠ WARNING"
        else:
            alert_text = "✅ NORMAL OPERATION"

        # ---------------- DASHBOARD OVERLAY ----------------
        cv2.putText(frame, f"STATUS: {alert_text}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, get_color(severity), 3)

        cv2.putText(frame, f"DEFECT COUNT: {len(defects)}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.putText(frame, f"SEVERITY: {severity}", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, get_color(severity), 2)

        # ---------------- STREAM ENCODE ----------------
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()