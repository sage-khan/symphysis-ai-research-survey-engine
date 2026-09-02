"""One-off helper: re-run exactly ONE agent card in an existing survey
without re-calling the provider for every other agent. Usage:
    PYTHONPATH=src python3 scripts/run_single_agent.py <survey_dir> <agent_id>
"""
from __future__ import annotations
import sys
from pathlib import Path
from symphysis.agent import Agent
from symphysis.agent_card import load_card
from symphysis.audit.logger import SurveyStorage
from symphysis.config import load_survey_config
from symphysis.orchestrator import INSTRUMENTS
from symphysis.spawning import spawn as agent_spawn

def main() -> None:
    survey_dir, agent_id = sys.argv[1], sys.argv[2]
    survey = load_survey_config(Path(survey_dir))
    storage = SurveyStorage(survey.root)
    instrument = INSTRUMENTS[survey.instrument]
    card_path = None
    for cp in survey.agent_cards:
        c = load_card(cp)
        if c.agent_id == agent_id:
            card_path = cp
            break
    if card_path is None:
        raise SystemExit(f'agent_id {agent_id!r} not found among {[load_card(c).agent_id for c in survey.agent_cards]}')
    card = load_card(card_path)
    agent_spawn.declare_root(storage, card, survey_id=survey.id, runtime_backend=card.runtime_backend)
    agent = Agent(card, card_path, storage)
    run = agent.run(instrument, survey.instrument_params, survey_title=survey.title, survey_description=survey.description, escalation=survey.escalation)
    print(f'agent={agent_id} accepted={len(run.accepted)} pending_manual={run.pending_manual}')

if __name__ == '__main__':
    main()
