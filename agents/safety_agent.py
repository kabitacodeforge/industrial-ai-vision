def safety_agent(defects):
    if len(defects) > 4:
        return "STOP_MACHINE"
    return "SAFE"