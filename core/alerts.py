def generate_alert(defects, machine_load, decision):

    if len(defects) > 3:
        return "🚨 CRITICAL DEFECT ALERT"

    if machine_load > 80:
        return "⚠ MACHINE OVERLOAD WARNING"

    if decision == "NORMAL_OPERATION":
        return "✅ SYSTEM STABLE"

    return "ℹ CHECK SYSTEM"