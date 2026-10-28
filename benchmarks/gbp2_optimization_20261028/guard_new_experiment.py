"""Enforce the human's finite experiment cap before any new GBP2 experiment."""
import json
from pathlib import Path

def check_new_experiment(root):
    path=root/'codex/GBP2_EXPERIMENT_LIMITS.json'
    assert path.exists(),'No explicit finite experiment authorization; read the current handoff'
    limits=json.loads(path.read_text(encoding='utf-8'))
    assert not limits['new_experiments_blocked'],'User experiment limit reached: finish current12 only; no new tests, probes, or repeats'
    used=sum((root/'benchmarks/results'/name).exists() for name in limits['counted_trials'])
    assert used<limits['max_new_formal_trials'],'Maximum number of authorized formal trials reached'
    return limits

if __name__=='__main__':
    check_new_experiment(Path('/mnt/d/STGPlanner'))
