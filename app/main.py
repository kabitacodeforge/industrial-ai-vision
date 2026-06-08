import cv2
from core.state import FactoryState
from core.factory_loop import run_factory
from vision.detector import detect

state = FactoryState()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO detection
    defects = detect(frame)
    state.defects = defects
    state.machine_load = len(defects) * 20

    decision, state = run_factory(frame, state)

    cv2.putText(frame, decision, (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)

    cv2.imshow("🏭 Multi-Agent Factory AI", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()