import json
import random
import re
from typing import Tuple, Set

from rdagent.app.qlib_rd_loop.conf import QUANT_PROP_SETTING
from rdagent.components.proposal import FactorAndModelHypothesisGen
from rdagent.core.proposal import Hypothesis, Scenario, Trace
from rdagent.oai.llm_utils import APIBackend
from rdagent.scenarios.qlib.proposal.bandit import (
    EnvController,
    extract_metrics_from_experiment,
)
from rdagent.utils.agent.tpl import T


class QuantTrace(Trace):
    def __init__(self, scen: Scenario) -> None:
        super().__init__(scen)
        # Initialize the controller with default weights
        self.controller = EnvController()


class QlibQuantHypothesis(Hypothesis):
    def __init__(
        self,
        hypothesis: str,
        reason: str,
        concise_reason: str,
        concise_observation: str,
        concise_justification: str,
        concise_knowledge: str,
        action: str,
    ) -> None:
        super().__init__(
            hypothesis, reason, concise_reason, concise_observation, concise_justification, concise_knowledge
        )
        self.action = action

    def __str__(self) -> str:
        return f"""Chosen Action: {self.action}
Hypothesis: {self.hypothesis}
Reason: {self.reason}
"""


class QlibQuantHypothesisGen(FactorAndModelHypothesisGen):
    def __init__(self, scen: Scenario) -> Tuple[dict, bool]:
        super().__init__(scen)

    def prepare_context(self, trace: Trace) -> Tuple[dict, bool]:

        # ========= Bandit ==========
        if QUANT_PROP_SETTING.action_selection == "bandit":
            if len(trace.hist) > 0:
                metric = extract_metrics_from_experiment(trace.hist[-1][0])
                prev_action = trace.hist[-1][0].hypothesis.action
                trace.controller.record(metric, prev_action)
                action = trace.controller.decide(metric)
            else:
                action = "factor"
        # ========= LLM ==========
        elif QUANT_PROP_SETTING.action_selection == "llm":
            hypothesis_and_feedback = (
                T("scenarios.qlib.prompts:hypothesis_and_feedback").render(trace=trace)
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

            system_prompt = T("scenarios.qlib.prompts:action_gen.system").r()
            user_prompt = T("scenarios.qlib.prompts:action_gen.user").r(
                hypothesis_and_feedback=hypothesis_and_feedback,
                last_hypothesis_and_feedback=last_hypothesis_and_feedback,
            )
            resp = APIBackend().build_messages_and_create_chat_completion(user_prompt, system_prompt, json_mode=True)

            action = json.loads(resp).get("action", "factor")
        # ========= random ==========
        elif QUANT_PROP_SETTING.action_selection == "random":
            action = random.choice(["factor", "model"])
        self.targets = action

        qaunt_rag = None
        if action == "factor":
            # ==================== [START] OPTIMIZED PROMPT LOGIC ====================
            # This new logic generates a staged, sophisticated prompt for the LLM.
            # It guides the AI from broad exploration to deep, innovative factor creation.
            
            num_factor_experiments = sum(1 for exp, _ in trace.hist if exp.hypothesis.action == "factor")

            if num_factor_experiments < 3:
                # Stage 1: Initial Exploration (Breadth-first)
                # Focus on foundational but advanced concepts.
                qaunt_rag = """
You are in the **initial exploration phase**. Your primary goal is to generate foundational, yet powerful, factors specifically designed for our advanced deep learning models (Transformers, ALSTM, TCN, GATs).
Refer to the `factor_hypothesis_specification` and propose hypotheses from at least two different core principles:
1.  **Advanced Time-Series Features**: Propose a factor capturing volatility dynamics or trend persistence (e.g., GARCH-like or Hurst-exponent-inspired features).
2.  **Cross-Sectional & Relational Features**: Propose a factor that measures a stock's relative strength against its industry peers (e.g., using `Rank()` or cross-sectional standardization).
This strategy will help us quickly map out promising research directions. Be bold and creative.
"""
            elif 3 <= num_factor_experiments < 8:
                # Stage 2: Refinement and Interaction (Depth-first)
                # Focus on combining and enhancing existing ideas.
                qaunt_rag = """
We have completed the initial mapping. Now, transition to a **refinement and interaction phase**. Your task is to build upon previous results to create more complex, second-order factors.
Analyze the historical feedback carefully:
- If a specific direction (e.g., volatility) has shown promise, **deepen the research**: Propose a more sophisticated variant or a refined parameterization of that factor.
- **Create interaction factors**: Combine concepts from different successful families. For example, propose a factor that interacts a momentum feature with a volatility feature (e.g., `Momentum / Volatility`).
- **Apply non-linear transformations**: Suggest using `Log()`, `Sqrt()`, or `Power()` on existing high-performing factors to capture non-linear relationships our DL models can exploit.
The goal is to unlock new alpha by combining and transforming what we've learned.
"""
            else:
                # Stage 3: Advanced Innovation
                # Push the boundaries with cutting-edge concepts.
                qaunt_rag = """
Our factor library is maturing. To achieve a new State-of-the-Art (SOTA), we must pursue **breakthrough innovations**. Your hypotheses should now focus on the most advanced and dynamic concepts.
Prioritize the following directions:
1.  **Market Regime-Adaptive Factors**: This is your top priority. Propose factors whose behavior or parameters (e.g., lookback window) dynamically adapt to the market state. For instance, a momentum factor that uses a shorter lookback in high-volatility regimes and a longer one in low-volatility regimes.
2.  **Graph-based Relational Factors**: For our GATs model, propose factors that explicitly model inter-stock relationships beyond simple industry grouping. Think about correlation networks or supply-chain relationships if data were available.
3.  **Information-Theoretic Features**: Propose factors based on concepts like information entropy of price movements to measure market uncertainty.
Your proposals must be novel and challenge conventional factor design. Do not re-propose simple variations of existing SOTA factors.
"""
            # ===================== [END] OPTIMIZED PROMPT LOGIC =====================
        elif action == "model":
            # ==================== [START] DYNAMIC MODEL EXPLORATION LOGIC ====================
            # This block dynamically generates the RAG prompt for model selection based on historical performance.
            # Its goal is to break out of local optima by forcing exploration of new architectures when stuck.

            # --- Configuration ---
            # A set of all supported model architectures. This is the universe of possibilities.
            SUPPORTED_MODELS: Set[str] = {"ALSTM", "Transformer", "LSTM", "GRU", "TCN", "TabNet", "SFM", "GATs"}
            # The number of consecutive failed model trials that triggers the "stagnation" state.
            STAGNATION_THRESHOLD: int = 3

            # --- State Analysis from History ---
            consecutive_model_failures = 0
            sota_found_in_history = False
            tried_model_types: Set[str] = set()
            sota_model_type = "N/A"

            # Helper to find a model keyword in text, case-insensitively.
            def find_model_type(text: str) -> str:
                for model_name in SUPPORTED_MODELS:
                    if re.search(r'\b' + re.escape(model_name) + r'\b', text, re.IGNORECASE):
                        return model_name
                return None

            # Iterate backwards through history to find the last model SOTA and count consecutive failures.
            for exp, feedback in reversed(trace.hist):
                if exp.hypothesis.action == "model":
                    model_type = find_model_type(exp.hypothesis.hypothesis)
                    if model_type:
                        tried_model_types.add(model_type)

                    if feedback.decision is True:
                        # Found the last SOTA model. Record its type and stop counting failures.
                        sota_found_in_history = True
                        sota_model_type = model_type or "Unknown"
                        break 
                    elif not sota_found_in_history:
                        # This is a failed model trial before the last SOTA was found.
                        consecutive_model_failures += 1
            
            # --- Dynamic RAG Prompt Generation ---
            is_stagnated = consecutive_model_failures >= STAGNATION_THRESHOLD

            if is_stagnated:
                # STATE: STAGNATED. Force exploration of new architectures.
                available_models_str = ", ".join(sorted(list(SUPPORTED_MODELS)))
                tried_models_str = ", ".join(sorted(list(tried_model_types))) if tried_model_types else "None"
                untried_models = SUPPORTED_MODELS - tried_model_types
                
                if untried_models:
                    untried_models_str = ", ".join(sorted(list(untried_models)))
                    instruction = (
                        f"Your primary task is to propose a model from the **UNTRIED** list: **[{untried_models_str}]**. "
                        f"You MUST select one of these to break the deadlock."
                    )
                else:
                    # All models have been tried. Shift strategy to re-evaluating the most different or promising ones.
                    instruction = (
                        "All available model architectures have been attempted. Your task is to re-evaluate and propose a model that is "
                        f"architecturally most different from the current {sota_model_type}-based SOTA. "
                        "For example, consider Transformer, TabNet, or GATs again, but with a fundamentally new hypothesis about why it might work now (e.g., new factors, different hyperparameters)."
                    )

                qaunt_rag = f"""
**CRITICAL DIRECTIVE: BREAK THE PERFORMANCE PLATEAU.**
The system has failed to produce a new SOTA model for the last **{consecutive_model_failures}** consecutive model trials. The current strategy of refining the **{sota_model_type}** model is stuck in a local optimum.

**Your mission is to propose a DIFFERENT model architecture to introduce new inductive biases.**

- **Full List of Available Architectures:** [{available_models_str}]
- **Historically Attempted Architectures:** [{tried_models_str}]

{instruction}

**DO NOT propose another {sota_model_type}-based model.** Your goal is exploration and novelty, not incremental refinement. Justify your choice by explaining why the new architecture is a promising alternative given the data and history.
"""
            else:
                # STATE: NOT STAGNATED. Standard refinement and adjacent exploration.
                qaunt_rag = f"""
1.  The current SOTA model is based on the **{sota_model_type}** architecture, which has proven effective. You can propose intelligent refinements to its hyperparameters (e.g., hidden size, dropout, learning rate) or minor architectural tweaks (e.g., adding a layer).
2.  You may also consider proposing models with similar inductive biases if you have a strong reason. For example, if GRU is working, LSTM is a reasonable alternative to explore.
3.  The training data consists of approximately 478,000 samples for the training set and about 128,000 samples for the validation set. Please design the hyperparameters accordingly and control the model size to ensure efficient training.
4.  Focus on a balanced approach: either refine the proven winner or take a small, logical step to a related architecture.
"""
            # ===================== [END] DYNAMIC MODEL EXPLORATION LOGIC =====================

        if len(trace.hist) == 0:
            hypothesis_and_feedback = "No previous hypothesis and feedback available since it's the first round."
        else:
            specific_trace = Trace(trace.scen)
            if action == "factor":
                # all factor experiments and the SOTA model experiment
                model_inserted = False
                for i in range(len(trace.hist) - 1, -1, -1):  # Reverse iteration
                    if trace.hist[i][0].hypothesis.action == "factor":
                        specific_trace.hist.insert(0, trace.hist[i])
                    elif (
                        trace.hist[i][0].hypothesis.action == "model"
                        and trace.hist[i][1].decision is True
                        and model_inserted == False
                    ):
                        specific_trace.hist.insert(0, trace.hist[i])
                        model_inserted = True
            elif action == "model":
                # all model experiments and all SOTA factor experiments
                factor_inserted = False
                for i in range(len(trace.hist) - 1, -1, -1):  # Reverse iteration
                    if trace.hist[i][0].hypothesis.action == "model":
                        specific_trace.hist.insert(0, trace.hist[i])
                    elif (
                        trace.hist[i][0].hypothesis.action == "factor"
                        and trace.hist[i][1].decision is True
                        and factor_inserted == False
                    ):
                        specific_trace.hist.insert(0, trace.hist[i])
                        factor_inserted = True
            if len(specific_trace.hist) > 0:
                specific_trace.hist.reverse()
                hypothesis_and_feedback = T("scenarios.qlib.prompts:hypothesis_and_feedback").r(
                    trace=specific_trace,
                )
            else:
                hypothesis_and_feedback = "No previous hypothesis and feedback available."

        last_hypothesis_and_feedback = None
        for i in range(len(trace.hist) - 1, -1, -1):
            if trace.hist[i][0].hypothesis.action == action:
                last_hypothesis_and_feedback = T("scenarios.qlib.prompts:last_hypothesis_and_feedback").r(
                    experiment=trace.hist[i][0], feedback=trace.hist[i][1]
                )
                break

        sota_hypothesis_and_feedback = None
        if action == "model":
            for i in range(len(trace.hist) - 1, -1, -1):
                if trace.hist[i][0].hypothesis.action == "model" and trace.hist[i][1].decision is True:
                    sota_hypothesis_and_feedback = T("scenarios.qlib.prompts:sota_hypothesis_and_feedback").r(
                        experiment=trace.hist[i][0], feedback=trace.hist[i][1]
                    )
                    break

        context_dict = {
            "hypothesis_and_feedback": hypothesis_and_feedback,
            "last_hypothesis_and_feedback": last_hypothesis_and_feedback,
            "SOTA_hypothesis_and_feedback": sota_hypothesis_and_feedback,
            "RAG": qaunt_rag,
            "hypothesis_output_format": T("scenarios.qlib.prompts:hypothesis_output_format_with_action").r(),
            "hypothesis_specification": (
                T("scenarios.qlib.prompts:factor_hypothesis_specification").r()
                if action == "factor"
                else T("scenarios.qlib.prompts:model_hypothesis_specification").r()
            ),
        }
        return context_dict, True

    def convert_response(self, response: str) -> Hypothesis:
        response_dict = json.loads(response)
        hypothesis = QlibQuantHypothesis(
            hypothesis=response_dict.get("hypothesis"),
            reason=response_dict.get("reason"),
            concise_reason=response_dict.get("concise_reason"),
            concise_observation=response_dict.get("concise_observation"),
            concise_justification=response_dict.get("concise_justification"),
            concise_knowledge=response_dict.get("concise_knowledge"),
            action=response_dict.get("action"),
        )
        return hypothesis