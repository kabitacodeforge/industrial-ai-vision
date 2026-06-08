from collections import deque
import time

# store last 50 records (like factory logs)
defect_history = deque(maxlen=50)
load_history = deque(maxlen=50)
decision_history = deque(maxlen=50)


def log_event(defects, load, decision):
    defect_history.append(len(defects))
    load_history.append(load)
    decision_history.append({
        "time": time.time(),
        "decision": decision
    })