from copy import deepcopy
from pathlib import Path

from rdagent.components.coder.factor_coder.factor import (
    FactorExperiment,
    FactorFBWorkspace,
    FactorTask,
)
from rdagent.core.experiment import Task
from rdagent.core.scenario import Scenario
from rdagent.scenarios.qlib.experiment.utils import get_data_folder_intro
from rdagent.scenarios.qlib.experiment.workspace import QlibFBWorkspace
from rdagent.utils.agent.tpl import T


class QlibFactorExperiment(FactorExperiment[FactorTask, QlibFBWorkspace, FactorFBWorkspace]):
    def __init__(self, *args, initial_stdout=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.experiment_workspace = QlibFBWorkspace(template_folder_path=Path(__file__).parent / "factor_template")
        self.stdout = initial_stdout if initial_stdout is not None else ""


class QlibFactorScenario(Scenario):
    def get_runtime_environment(self) -> str:
        return "python:3.10-slim, qlib"

    def __init__(self) -> None:
        super().__init__()
        self._background = deepcopy(T(".prompts:qlib_factor_background").r())
        self._source_data = deepcopy(get_data_folder_intro())
        self._output_format = deepcopy(T(".prompts:qlib_factor_output_format").r())
        self._interface = deepcopy(T(".prompts:qlib_factor_interface").r())
        self._strategy = deepcopy(T(".prompts:qlib_factor_strategy").r())
        self._simulator = deepcopy(T(".prompts:qlib_factor_simulator").r())
        self._rich_style_description = deepcopy(T(".prompts:qlib_factor_rich_style_description").r())
        self._experiment_setting = deepcopy(T(".prompts:qlib_factor_experiment_setting").r())

    @property
    def background(self) -> str:
        return self._background

    def get_source_data_desc(self, task: Task | None = None) -> str:
        return self._source_data

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
        """A static scenario describer"""
        if simple_background:
            return f"""Background of the scenario:
{self.background}"""
        return f"""Background of the scenario:
{self.background}
The source data you can use:
{self.get_source_data_desc(task)}
The interface you should follow to write the runnable code:
{self.interface}

------Crucial Output Format Constraints------
You MUST respond with a single, valid JSON object. 
Crucially, all values in this JSON object MUST be strings. Do not use nested JSON objects or arrays as values. If a value contains complex information, format it as a multi-line string.

**GOOD Example (Correct Format):**
{{
  "factor_name": "VolatilityRegimeIndicator_20_60",
  "factor_description": "This factor aims to identify volatility regimes by comparing short-term volatility with long-term volatility.",
  "factor_formulation": "(Short-term Volatility / Long-term Volatility) - 1",
  "factor_variables": "{{\\n  \\"close\\": \\"The daily closing price of the instrument.\\",\\n  \\"daily_return\\": \\"The daily percentage change in the closing price, calculated as (close_t / close_{{t-1}}) - 1.\\",\\n  \\"short_term_window\\": \\"20 days\\",\\n  \\"long_term_window\\": \\"60 days\\"\\n}}"
}}

**BAD Example (Incorrect Format - DO NOT USE):**
{{
  "factor_name": "VolatilityRegimeIndicator_20_60",
  "factor_description": "This factor aims to identify volatility regimes...",
  "factor_formulation": "(Short-term Volatility / Long-term Volatility) - 1",
  "factor_variables": {{  // <-- INCORRECT! This is a nested object, not a string.
    "close": "The daily closing price...",
    "daily_return": "The daily percentage change...",
    "short_term_window": 20, // <-- INCORRECT! This is a number, not a string.
    "long_term_window": 60
  }}
}}

The output of your code should be in the format:
{self.output_format}
The simulator user can use to test your factor:
{self.simulator}
"""
