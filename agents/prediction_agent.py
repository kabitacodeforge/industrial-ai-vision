def prediction_agent(defects):
    if len(defects) > 3:
        return "FAILURE_RISK"
    return "STABLE"