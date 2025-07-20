import unittest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from rdagent.scenarios.qlib.developer.model_runner import QlibModelRunner
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelExperiment
from rdagent.components.coder.model_coder.model import ModelTask, ModelFBWorkspace
from rdagent.core.conf import RD_AGENT_SETTINGS


class TestModelRunner(unittest.TestCase):
    def setUp(self):
        RD_AGENT_SETTINGS.cache_with_pickle = False

    def tearDown(self):
        RD_AGENT_SETTINGS.cache_with_pickle = True

    def test_num_timesteps_propagation(self):
        task = ModelTask(
            name="TestModel",
            description="desc",
            architecture="arch",
            hyperparameters={"num_timesteps": 240},
            training_hyperparameters={},
            model_type="TimeSeries",
        )
        exp = QlibModelExperiment(sub_tasks=[task])
        exp.sub_workspace_list[0] = ModelFBWorkspace(target_task=task)
        exp.sub_workspace_list[0].file_dict = {"model.py": "print('hello')"}

        runner = QlibModelRunner(None)

        with patch.object(exp.experiment_workspace, "execute", return_value=(1, "")) as mock_exec:
            runner.develop(exp)
            kwargs = mock_exec.call_args.kwargs
            env = kwargs.get("run_env", {})
            self.assertEqual(env.get("num_timesteps"), "240")
            self.assertEqual(env.get("step_len"), "240")


if __name__ == "__main__":
    unittest.main()
