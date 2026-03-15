import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from verticals.bitnin.services.bitnin_runtime_runner.runner import BitNinRuntimeRunner

@pytest.fixture
def mock_runner():
    with patch("verticals.bitnin.services.bitnin_runtime_runner.runner.BitNinAnalyst") as mock_analyst_cls, \
         patch("verticals.bitnin.services.bitnin_runtime_runner.runner.BitNinShadowRunner") as mock_shadow_cls, \
         patch("verticals.bitnin.services.bitnin_runtime_runner.runner.BitNinHitlRunner") as mock_hitl_cls, \
         patch("verticals.bitnin.services.bitnin_runtime_runner.runner.BitNinExecGuardRunner") as mock_exec_cls, \
         patch("verticals.bitnin.services.bitnin_runtime_runner.runner.ObservabilityBuilder") as mock_obs_cls:
        
        # Setup mocks
        mock_analyst = mock_analyst_cls.return_value
        mock_analyst.build.return_value = {"normalized_path": "mock_analysis.json"}
        
        mock_shadow = mock_shadow_cls.return_value
        mock_shadow.run.return_value = {"intent_path": "mock_intent.json"}
        
        mock_hitl = mock_hitl_cls.return_value
        mock_hitl.request.return_value = {"approval_id": "app_1", "request_path": "mock_approval.json"}
        mock_hitl.decide.return_value = {"status": "approved", "decision_path": "mock_decision.json"}
        
        mock_exec = mock_exec_cls.return_value
        mock_exec.run.return_value = {"record_path": "mock_record.json"}
        
        mock_obs = mock_obs_cls.return_value
        mock_obs.health.check.return_value = {"overall": "UP", "checks": []}
        
        runner = BitNinRuntimeRunner()
        return runner

def test_run_once_success(mock_runner):
    result = mock_runner.run_once(auto_approve=True)
    
    assert "replay_id" in result
    assert len(result["points"]) > 0
    # Verify sequence
    mock_runner.analyst.build.assert_called_once()
    mock_runner.shadow.run.assert_called_once()
    mock_runner.hitl.request.assert_called_once()
    mock_runner.exec_guard.run.assert_called_once()
    # Should call hitl.decide
    mock_runner.hitl.decide.assert_called_once()
    # Should have registered observability
    mock_runner.obs.replay.register_replay.assert_called_once()

def test_run_once_without_auto_approve(mock_runner):
    result = mock_runner.run_once(auto_approve=False)
    
    assert "replay_id" in result
    # Should stop before exec_guard if not approved
    mock_runner.exec_guard.run.assert_not_called()
    # Should still register observability
    mock_runner.obs.replay.register_replay.assert_called_once()

def test_run_once_handles_error(mock_runner):
    mock_runner.analyst.build.side_effect = Exception("Analyst failed")
    
    result = mock_runner.run_once()
    
    # Should contain error event
    events = [p["event"] for p in result["points"]]
    assert "error" in events
    # Should still register observability
    mock_runner.obs.replay.register_replay.assert_called_once()
