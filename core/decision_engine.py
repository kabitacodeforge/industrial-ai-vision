def decision_engine(actions):

    if "STOP_MACHINE" in actions:
        return "🛑 STOP MACHINE"

    if "FAILURE_RISK" in actions:
        return "⚠️ MAINTENANCE REQUIRED"

    if "POWER_SAVING" in actions:
        return "⚡ REDUCE ENERGY"

    if "HIGH_DEFECT" in actions:
        return "🔧 SLOW PRODUCTION"

    return "✅ NORMAL OPERATION"