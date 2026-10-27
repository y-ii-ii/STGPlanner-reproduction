"""Classify raw results without turning interruptions into completed trials."""
import json
import math

def classify_outcome(folder, result):
    reason = result['finish_reason']
    pause_path = folder / 'user_pause.json'
    if pause_path.exists():
        pause = json.loads(pause_path.read_text())
        assert pause['state'] == 'paused_by_user'
        assert pause['trial'] == result['trial']
        assert pause['intentional_native_stop'] is True
        assert pause['reached_common_threshold'] is False
        assert pause['result_finish_reason'] == reason
        assert math.isclose(pause['sim_time_s'], result['sim_time_s'], abs_tol=1e-6)
        assert math.isclose(pause['coverage_fraction'], result['coverage_fraction'], abs_tol=1e-9)
        assert reason in ('process_exit:native_planner', 'native_node_unresponsive')
        assert result['validation']['reached_common_threshold'] is False
        return 'user_interrupted'
    if reason == 'coverage_threshold':
        assert result['area_m2'] > result['area_threshold_m2']
        return 'common_threshold_reached'
    if reason == 'sim_time_limit':
        assert result['sim_time_s'] >= result['sim_time_limit_s']
        return 'complete_time_limit_observation'
    interruption_path = folder / 'interruption.json'
    if interruption_path.exists():
        interruption = json.loads(interruption_path.read_text())
        assert interruption['intentional_native_stop'] is True
        assert reason in ('process_exit:native_planner', 'native_node_unresponsive')
        return 'intentional_diagnostic_stop'
    return 'abnormal_stop'
