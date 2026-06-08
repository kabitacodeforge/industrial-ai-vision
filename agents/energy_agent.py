def energy_agent(load):
    if load > 80:
        return "POWER_SAVING"
    return "NORMAL_POWER"