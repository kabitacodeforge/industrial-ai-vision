def predict_risk(defects, machine_load):

    # base risk from defects
    defect_risk = len(defects) * 15

    # machine stress factor
    load_risk = machine_load * 0.6

    # total risk score
    risk_score = defect_risk + load_risk

    if risk_score > 80:
        return "HIGH RISK"

    elif risk_score > 40:
        return "MEDIUM RISK"

    else:
        return "LOW RISK"