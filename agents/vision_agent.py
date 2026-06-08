def vision_agent(defects):
    if len(defects) > 5:
        return "HIGH_DEFECT"
    elif len(defects) > 2:
        return "MEDIUM_DEFECT"
    return "OK"