import json
import re
from typing import List, Tuple, Set

from rdagent.components.coder.model_coder.model import ModelExperiment, ModelTask
from rdagent.components.proposal import ModelHypothesis2Experiment, ModelHypothesisGen
from rdagent.core.proposal import Hypothesis, Scenario, Trace
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelExperiment
from rdagent.scenarios.qlib.experiment.quant_experiment import QlibQuantScenario
from rdagent.utils.agent.tpl import T

QlibModelHypothesis = Hypothesis


class QlibModelHypothesisGen(ModelHypothesisGen):
    def __init__(self, scen: Scenario) -> Tuple[dict, bool]:
        super().__init__(scen)

    def prepare_context(self, trace: Trace) -> Tuple[dict, bool]:
        hypothesis_and_feedback = (
            T("scenarios.qlib.prompts:hypothesis_and_feedback").r(
                trace=trace,
            )
            if len(trace.hist) > 0
            else "No previous hypothesis and feedback available since it's the first round."
        )

        last_hypothesis_and_feedback = (
            T("scenarios.qlib.prompts:last_hypothesis_and_feedback").r(
                experiment=trace.hist[-1][0], feedback=trace.hist[-1][1]
            )
            if len(trace.hist) > 0
            else "No previous hypothesis and feedback available since it's the first round."
        )

        sota_hypothesis_and_feedback = ""
        if len(trace.hist) == 0:
            sota_hypothesis_and_feedback = "No SOTA hypothesis and feedback available since it is the first round."
        else:
            for i in range(len(trace.hist) - 1, -1, -1):
                if trace.hist[i][1].decision:
                    sota_hypothesis_and_feedback = T("scenarios.qlib.prompts:sota_hypothesis_and_feedback").r(
                        experiment=trace.hist[i][0], feedback=trace.hist[i][1]
                    )
                    break
            else:
                sota_hypothesis_and_feedback = (
                    "No SOTA hypothesis and feedback available since previous experiments were not accepted."
                )

        # ==================== [START] DYNAMIC MODEL EXPLORATION LOGIC (ARCHITECT MODIFIED & SYNCED) ====================
        # This block dynamically generates the RAG prompt for model selection based on historical performance.
        # It is an identical copy of the logic from `quant_proposal.py` to ensure consistent behavior
        # when running the dedicated `fin_model` scenario.

        # --- Configuration ---
        SUPPORTED_MODELS: Set[str] = {
            "ALSTM", "LSTM", "GRU", "TCN", "Transformer", "LocalFormer", "TCTS",
            "TabNet", "SFM", "Sandwich", "Hist", "IGMTF", "KRNN", "TRA",
            "GATs", "LightGBM", "XGBoost", "CatBoost", "GBDT", "Linear"
        }
        STAGNATION_THRESHOLD: int = 3

        # --- State Analysis from History ---
        consecutive_model_failures = 0
        sota_found_in_history = False
        tried_model_types: Set[str] = set()
        sota_model_type = "N/A"

        def find_model_type(text: str) -> str:
            sorted_models = sorted(list(SUPPORTED_MODELS), key=len, reverse=True)
            for model_name in sorted_models:
                if re.search(r'\b' + re.escape(model_name) + r'\b', text, re.IGNORECASE):
                    return model_name
            return None

        # Iterate backwards through the history, which in this scenario consists only of model experiments.
        for exp, feedback in reversed(trace.hist):
            # The check for `action == "model"` is implicitly true here, but we keep the logic identical for robustness.
            model_type = find_model_type(exp.hypothesis.hypothesis) or find_model_type(exp.sub_tasks[0].name)
            if model_type:
                tried_model_types.add(model_type)

            if feedback.decision is True:
                sota_found_in_history = True
                sota_model_type = model_type or "Unknown"
                break
            elif not sota_found_in_history:
                consecutive_model_failures += 1
        
        # --- Dynamic RAG Prompt Generation ---
        is_stagnated = consecutive_model_failures >= STAGNATION_THRESHOLD
        dynamic_rag = ""

        if is_stagnated:
            # STATE: STAGNATED. Generate a strong, directive prompt to force exploration.
            untried_models = SUPPORTED_MODELS - tried_model_types
            
            available_models_str = ", ".join(sorted(list(SUPPORTED_MODELS)))
            tried_models_str = ", ".join(sorted(list(tried_model_types))) if tried_model_types else "None"
            untried_models_str = ", ".join(sorted(list(untried_models))) if untried_models else "None"

            if untried_models:
                instruction = f"Your primary task is to propose a model from the **UNTRIED** list: **[{untried_models_str}]**. Explain why your chosen architecture's inductive bias is suitable for financial time-series and different from what we've tried."
            else:
                instruction = "All model architectures have been tried. Your task is to re-evaluate and propose a model that is architecturally most different from the current GRU-based SOTA, or one that showed promise in the past but was not SOTA. For example, consider **Transformer** or **GATs** again with a new hypothesis."

            dynamic_rag = f"""
**CRITICAL DIRECTIVE: BREAK THE PERFORMANCE PLATEAU.**
The system has failed to produce a new SOTA model for the last **{consecutive_model_failures}** consecutive model trials. The current strategy of refining the **{sota_model_type}** model is stuck in a local optimum and must be abandoned.

**Your mission is to propose a completely different model architecture to introduce new inductive biases.**

- **Full List of Available Architectures:** [{available_models_str}]
- **Historically Attempted Architectures:** [{tried_models_str}]

{instruction}

Do **NOT** propose another `{sota_model_type}`-based model. Focus on novelty and systematic exploration. A well-justified proposal for a new architecture is more valuable than a marginal improvement on the old one.
"""
        else:
            # STATE: NOT STAGNATED. Standard refinement and adjacent exploration.
            dynamic_rag = f"""
1.  The current SOTA model is based on the **{sota_model_type}** architecture, which has proven effective. You can propose intelligent refinements to its hyperparameters (e.g., hidden size, dropout, learning rate) or minor architectural tweaks (e.g., adding a layer).
2.  You may also consider proposing models with similar inductive biases if you have a strong reason. For example, if GRU is working, **LSTM** or **TCN** are reasonable alternatives to explore.
3.  The training data consists of approximately 478,000 samples for the training set and about 128,000 samples for the validation set. Please design the hyperparameters accordingly and control the model size to ensure efficient training.
4.  Focus on a balanced approach: either refine the proven winner or take a small, logical step to a related architecture.
"""
        # ===================== [END] DYNAMIC MODEL EXPLORATION LOGIC =====================

        context_dict = {
            "hypothesis_and_feedback": hypothesis_and_feedback,
            "last_hypothesis_and_feedback": last_hypothesis_and_feedback,
            "SOTA_hypothesis_and_feedback": sota_hypothesis_and_feedback,
            "RAG": dynamic_rag, # Use the newly generated dynamic RAG prompt
            "hypothesis_output_format": T("scenarios.qlib.prompts:hypothesis_output_format").r(),
            "hypothesis_specification": T("scenarios.qlib.prompts:model_hypothesis_specification").r(),
        }
        return context_dict, True

    def convert_response(self, response: str) -> Hypothesis:
        response_dict = json.loads(response)
        hypothesis = QlibModelHypothesis(
            hypothesis=response_dict.get("hypothesis"),
            reason=response_dict.get("reason"),
            concise_reason=response_dict.get("concise_reason"),
            concise_observation=response_dict.get("concise_observation"),
            concise_justification=response_dict.get("concise_justification"),
            concise_knowledge=response_dict.get("concise_knowledge"),
        )
        return hypothesis


class QlibModelHypothesis2Experiment(ModelHypothesis2Experiment):
    def prepare_context(self, hypothesis: Hypothesis, trace: Trace) -> Tuple[dict, bool]:
        if isinstance(trace.scen, QlibQuantScenario):
            scenario = trace.scen.get_scenario_all_desc(action="model")
        else:
            scenario = trace.scen.get_scenario_all_desc()
        experiment_output_format = T("scenarios.qlib.prompts:model_experiment_output_format").r()

        last_experiment = None
        last_feedback = None
        sota_experiment = None
        sota_feedback = None

        if len(trace.hist) == 0:
            hypothesis_and_feedback = "No previous hypothesis and feedback available since it's the first round."
        else:
            specific_trace = Trace(trace.scen)
            for i in range(len(trace.hist) - 1, -1, -1):  # Reverse iteration
                # Simplified logic for model-only scenario
                if last_experiment is None:
                    last_experiment = trace.hist[i][0]
                    last_feedback = trace.hist[i][1]
                if trace.hist[i][1].decision is True and sota_experiment is None:
                    sota_experiment = trace.hist[i][0]
                    sota_feedback = trace.hist[i][1]
                specific_trace.hist.insert(0, trace.hist[i])

            if len(specific_trace.hist) > 0:
                specific_trace.hist.reverse()
                hypothesis_and_feedback = T("scenarios.qlib.prompts:hypothesis_and_feedback").r(
                    trace=specific_trace,
                )
            else:
                hypothesis_and_feedback = "No previous hypothesis and feedback available."

        last_hypothesis_and_feedback = (
            T("scenarios.qlib.prompts:last_hypothesis_and_feedback").r(
                experiment=last_experiment, feedback=last_feedback
            )
            if last_experiment is not None
            else "No previous hypothesis and feedback available since it's the first round."
        )

        sota_hypothesis_and_feedback = (
            T("scenarios.qlib.prompts:sota_hypothesis_and_feedback").r(
                experiment=sota_experiment, feedback=sota_feedback
            )
            if sota_experiment is not None
            else "No SOTA hypothesis and feedback available since previous experiments were not accepted."
        )

        experiment_list: List[ModelExperiment] = [t[0] for t in trace.hist]

        model_list = []
        for experiment in experiment_list:
            model_list.extend(experiment.sub_tasks)

        return {
            "target_hypothesis": str(hypothesis),
            "scenario": scenario,
            "hypothesis_and_feedback": hypothesis_and_feedback,
            "last_hypothesis_and_feedback": last_hypothesis_and_feedback,
            "SOTA_hypothesis_and_feedback": sota_hypothesis_and_feedback,
            "experiment_output_format": experiment_output_format,
            "target_list": model_list,
            "RAG": "Note, the training data consists of less than 1 million samples for the training set and approximately 250,000 samples for the validation set. Please design the hyperparameters accordingly and control the model size. This has a significant impact on the training results. If you believe that the previous model itself is good but the training hyperparameters or model hyperparameters are not optimal, you can return the same model and adjust these parameters instead.",
        }, True

    def convert_response(self, response: str, hypothesis: Hypothesis, trace: Trace) -> ModelExperiment:
        response_dict = json.loads(response)
        tasks = []
        for model_name in response_dict:
            description = response_dict[model_name]["description"]
            formulation = response_dict[model_name]["formulation"]
            architecture = response_dict[model_name]["architecture"]
            variables = response_dict[model_name]["variables"]
            hyperparameters = response_dict[model_name]["hyperparameters"]
            training_hyperparameters = response_dict[model_name]["training_hyperparameters"]
            model_type = response_dict[model_name]["model_type"]
            tasks.append(
                ModelTask(
                    name=model_name,
                    description=description,
                    formulation=formulation,
                    architecture=architecture,
                    variables=variables,
                    hyperparameters=hyperparameters,
                    training_hyperparameters=training_hyperparameters,
                    model_type=model_type,
                )
            )
        exp = QlibModelExperiment(tasks, hypothesis=hypothesis)
        exp.based_experiments = [t[0] for t in trace.hist if t[1]]
        return exp