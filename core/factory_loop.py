from agents.vision_agent import vision_agent
from agents.safety_agent import safety_agent
from agents.energy_agent import energy_agent
from agents.prediction_agent import prediction_agent
from core.decision_engine import decision_engine


def run_factory(frame, state):

    defects = getattr(state, "defects", [])
    load = getattr(state, "machine_load", 50)

    actions = []

    actions.append(vision_agent(defects))
    actions.append(safety_agent(defects))
    actions.append(energy_agent(load))
    actions.append(prediction_agent(defects))

    decision = decision_engine(actions)

    return decision, state