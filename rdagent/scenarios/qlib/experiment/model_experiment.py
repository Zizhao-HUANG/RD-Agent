from copy import deepcopy
from pathlib import Path

from rdagent.components.coder.model_coder.model import (
    ModelExperiment,
    ModelFBWorkspace,
    ModelTask,
)
from rdagent.core.experiment import Task
from rdagent.core.scenario import Scenario
from rdagent.scenarios.qlib.experiment.workspace import QlibFBWorkspace
from rdagent.utils.agent.tpl import T


class QlibModelExperiment(ModelExperiment[ModelTask, QlibFBWorkspace, ModelFBWorkspace]):
    def __init__(self, *args, initial_stdout=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.experiment_workspace = QlibFBWorkspace(template_folder_path=Path(__file__).parent / "model_template")
        self.stdout = initial_stdout if initial_stdout is not None else ""


class QlibModelScenario(Scenario):
    def __init__(self) -> None:
        super().__init__()
        self._background = deepcopy(T(".prompts:qlib_model_background").r())
        self._output_format = deepcopy(T(".prompts:qlib_model_output_format").r())
        self._interface = deepcopy(T(".prompts:qlib_model_interface").r())
        self._simulator = deepcopy(T(".prompts:qlib_model_simulator").r())
        self._rich_style_description = deepcopy(T(".prompts:qlib_model_rich_style_description").r())
        self._experiment_setting = deepcopy(T(".prompts:qlib_model_experiment_setting").r())

    def get_runtime_environment(self) -> str:
        return "python:3.10-slim, qlib"

    @property
    def background(self) -> str:
        return self._background

    @property
    def source_data(self) -> str:
        raise NotImplementedError("source_data of QlibModelScenario is not implemented")

    @property
    def output_format(self) -> str:
        return self._output_format

    @property
    def interface(self) -> str:
        return self._interface

    @property
    def simulator(self) -> str:
        return self._simulator

    @property
    def rich_style_description(self) -> str:
        return self._rich_style_description

    @property
    def experiment_setting(self) -> str:
        return self._experiment_setting

    def get_scenario_all_desc(
        self, task: Task | None = None, filtered_tag: str | None = None, simple_background: bool | None = None
    ) -> str:
        return f"""Background of the scenario:
{self.background}
The interface you should follow to write the runnable code:
{self.interface}

------Crucial Output Format Constraints------
You MUST respond with a single, valid JSON object. 
Crucially, all values in this JSON object MUST be strings. Do not use nested JSON objects or arrays as values. If a value contains complex information, format it as a multi-line string.

**GOOD Example (Correct Format):**
{{
  "model_name": "TransformerTS_256_6",
  "model_description": "This model uses a transformer architecture for time series prediction.",
  "model_formulation": "y = Transformer(x)",
  "model_variables": "{{\\n  \\"x\\": \\"Input tensor with shape (batch_size, num_timesteps, num_features).\\",\\n  \\"y\\": \\"Output tensor with shape (batch_size, 1).\\",\\n  \\"d_model\\": \\"256\\",\\n  \\"num_layers\\": \\"6\\"\\n}}"
}}

**BAD Example (Incorrect Format - DO NOT USE):**
{{
  "model_name": "TransformerTS_256_6",
  "model_description": "This model uses a transformer architecture...",
  "model_formulation": "y = Transformer(x)",
  "model_variables": {{  // <-- INCORRECT! This is a nested object, not a string.
    "x": "Input tensor...",
    "y": "Output tensor...",
    "d_model": 256, // <-- INCORRECT! This is a number, not a string.
    "num_layers": 6
  }}
}}

The output of your code should be in the format:
{self.output_format}
The simulator user can use to test your model:
{self.simulator}
"""
