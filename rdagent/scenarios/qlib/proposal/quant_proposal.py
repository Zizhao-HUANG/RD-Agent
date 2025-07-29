import json
import random
from typing import Tuple

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
                T("scenarios.qlib.prompts:hypothesis_and_feedback").r(trace=trace)
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
            # ==================================================================
            # START: REVISED FACTOR RAG WITH 5-PHASE STRATEGIC METHODOLOGY
            # This RAG implements the user-defined, highly structured research plan.
            # ==================================================================
            num_factor_experiments = sum(1 for exp, _ in trace.hist if exp.hypothesis.action == "factor")

            FACTOR_CATEGORIES = [
                "Momentum and Reversal", "Volatility and Risk", "Price-Volume Interaction",
                "Intraday Price Patterns", "Higher-Order Derivatives and Transformations",
                "Cross-Sectional Relative Value", "Liquidity and Market Impact",
                "Return Distribution Skewness & Kurtosis", "Regime-Dependent / Conditional Factors",
                "Proxy for Fundamental Quality", "Proxy for Information Asymmetry & Informed Trading",
                "Proxy for Investor Sentiment & Behavior", "Proxy for Corporate Actions & Special Events",
                "Proxy for Investment Style Profile", "Proxy for Systemic Risk Contribution & Connectivity"
            ]
            
            # Phase 1: Initial Scan (Rounds 0-14, 15 experiments total)
            if num_factor_experiments < 15:
                qaunt_rag = f"""
                **Phase 1: Initial Scan (Round {num_factor_experiments + 1}/15).**
                **Goal:** Generate one baseline factor for each of the 15 conceptual categories, one per round.
                - **Your Task:** Propose **1 factor**. The factor must come from a category that has not been covered yet in this phase.
                - **Constraint:** The proposed factor must be **simple and easy to code**. We are prioritizing breadth and speed.
                - **Reference List of Categories:** {FACTOR_CATEGORIES}

                {{
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }}
                """
            # Phase 2: First Optimization Pass (Rounds 15-29, 15 experiments total)
            elif num_factor_experiments < 30:
                qaunt_rag = f"""
                **Phase 2: First Optimization Pass (Round {num_factor_experiments - 14}/15).**
                **Goal:** Systematically optimize the 15 baseline factors created in Phase 1, one per round.
                - **Your Task:** Review the feedback from the Phase 1 experiments. Select **1 factor** from that initial set and propose a specific optimization for it based on the results.
                - **Constraint:** Focus on refining the original 15 ideas. Do not introduce entirely new concepts yet.

                {{
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }}
                """
            # Phase 3: Deep Optimization of High-Potential Factors (Rounds 30-34, 5 experiments total)
            elif num_factor_experiments < 35:
                qaunt_rag = f"""
                **Phase 3: Deep Optimization of High-Potential Factors (Round {num_factor_experiments - 29}/5).**
                **Goal:** Systematically enhance the most promising factors from the first two phases.
                - **Your Task:** In each of these 5 rounds, analyze the performance of factors from Phases 1 & 2, and the ongoing optimizations within Phase 3. Select the **top 3-5 factors** that show the highest potential for alpha. Propose **advanced optimizations** for these selected factors.
                - **Constraint:** You can **significantly increase complexity** to capture deeper, more nuanced features. Focus on quality and impact. The number of factors you optimize in each round is flexible, but aim for a focused effort on the most promising ones.

                {{
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }}
                """
            # Phase 4: Focused Iterative Enhancement (Rounds 35-39, 5 experiments total)
            elif num_factor_experiments < 40:
                qaunt_rag = f"""
                **Phase 4: Focused Iterative Enhancement (Round {num_factor_experiments - 34}/5).**
                **Goal:** Further polish the high-potential factors identified and enhanced in Phase 3.
                - **Your Task:** Based on the comprehensive results from Phase 3, select a subset of those factors that show promise for even further improvement. Propose **3 new optimizations** for them.
                - **Constraint:** Continue to **increase complexity if necessary**. This could involve creating more sophisticated interactions, applying non-linear transformations, or making them regime-aware.

                {{
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }}
                """
            # Phase 5: Unrestricted Deep Dive (Round 40 onwards)
            else:
                qaunt_rag = f"""
                **Phase 5: Unrestricted Deep Dive (Round {num_factor_experiments - 39}).**
                **Goal:** Synthesize all learnings and achieve a breakthrough in alpha discovery by thinking from first principles.
                - **Your Task:** The structured research phases are complete. You now have full creative freedom. Deeply analyze the entire experimental history to understand what has worked and what has failed. Then, step back and formulate your boldest hypotheses by drawing inspiration from fundamental disciplines.
                - **Constraint:** **There are no restrictions.** Your objective is to invent the next State-of-the-Art alpha by proposing a novel, core insight about market behavior.

                ---
                ### **Cross-Disciplinary Inspiration Library**
                To spark a breakthrough, frame market behavior through the lens of another fundamental discipline. Use these mental models to generate entirely new hypotheses about *how markets truly work*.

                **Systems & Physics-Based Models:**
                *   **Complex Systems Science:** How do simple, local interactions between traders lead to complex, emergent market-wide phenomena (like crashes or bubbles)? Where are the tipping points?
                *   **Fluid Dynamics:** Can we view order flow and liquidity as a fluid? Where do we see smooth "laminar flow" (trends) versus chaotic "turbulence" (volatility)?
                *   **Information Theory:** What is the true signal-to-noise ratio of price movements? How can we measure the flow of information, its entropy, and its distortion within the market?

                **Human & Collective Behavior Models:**
                *   **Cognitive & Behavioral Psychology:** How do systemic, non-rational human biases (like loss aversion, herd instinct, or recency bias) manifest as predictable inefficiencies at a market scale?
                *   **Social Network Theory:** How does information, influence, and sentiment propagate through the network of investors? Can we identify the key nodes and the speed of diffusion?
                *   **Neuroscience:** Does the market as a whole exhibit cognitive functions like "attention" (focus on specific narratives) or "memory" (long-term price patterns)? How do these collective functions shift?
                *   **Epidemiology:** How do investment ideas and narratives spread like a virus? Can we model their "contagion rate" and identify them in their "incubation period" before they become mainstream?

                **Strategy & Evolution Models:**
                *   **Ecology & Evolutionary Dynamics:** If trading strategies are "species" competing for the "resource" of alpha, how does this ecosystem evolve? How can we measure a strategy's "crowdedness" or "niche"?
                *   **Game Theory:** What strategic "game" are market participants currently playing? How are they anticipating each other's moves, especially in situations involving liquidity or information asymmetry?

                **Meta-Level & Structural Models:**
                *   **Linguistics:** Is there a "grammar" to price action? Can we interpret sequences of price patterns as a language with its own syntax, predicting the next "word" or "phrase"?
                *   **Philosophy:** What is a core, unexamined assumption we hold about markets (e.g., about efficiency, rationality, or value)? What new hypothesis emerges if we challenge it directly?

                {{
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }}
                """
            # ==================================================================
            # END: REVISED FACTOR RAG LOGIC
            # ==================================================================
      
        elif action == "model":
            # ==================================================================
            # START: REVISED MODEL RAG WITH HIGH-LEVEL DIRECTIONAL GUIDANCE
            # This RAG provides strategic direction on the *type* of architecture to explore,
            # without recommending specific model names.
            # ==================================================================
            
            # Count the number of previous model experiments to guide the phased strategy
            num_model_experiments = sum(1 for exp, _ in trace.hist if exp.hypothesis.action == "model")

            if num_model_experiments < 7:
                # Phase 1: Focus on foundational time-series properties.
                qaunt_rag = """
                **Phase 1: Foundational Modeling.**
                Your primary goal is to establish a robust performance baseline by modeling fundamental time-series properties.
                - **Strategic Direction:** Focus on architectures designed for **sequential data processing**. These models are adept at capturing local temporal dependencies (like momentum) and are essential for confirming that basic patterns can be learned before attempting more complex structures.
                - **Goal:** Achieve a solid, difficult-to-beat baseline. Fine-tuning hyperparameters on these foundational architectures is a key strategy here.

                {
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }
                """
            elif num_model_experiments < 12:
                # Phase 2: Explore more complex, long-range patterns.
                qaunt_rag = """
                **Phase 2: Advanced Pattern Recognition.**
                The baselines are set. Now, you must push the performance limits by exploring more powerful architectural paradigms.
                - **Strategic Direction:** Shift focus to architectures capable of capturing **long-range and non-local dependencies**. These models can identify complex relationships across distant time steps that simpler sequential models might miss.
                - **Goal:** Leverage our powerful hardware to explore computationally intensive but potentially more expressive architectures. The aim is to find patterns that are not obvious or sequential.

                {
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }
                """
            else:
                # Phase 3: Focus on system-level improvements and novel strategies.
                qaunt_rag = """
                **Phase 3: Meta-Strategies and Frontier Research.**
                Single models may be reaching their limits. The focus must now shift from optimizing a single architecture to optimizing the overall prediction strategy.
                - **Primary Direction: Ensembling.** Propose **meta-strategies that combine the predictions of multiple, diverse, and previously successful models**. The goal is to improve robustness, reduce prediction variance, and create a more stable system, which is often more valuable than a marginal gain in a single metric.
                - **Secondary Direction: Hybrid Architectures.** Explore models that creatively **fuse different concepts**, such as combining the feature extraction power of tabular models with the dynamic awareness of time-series models.
                - **Research Frontier: Relational Modeling.** As a high-risk option, consider a paradigm shift towards models that can learn from **inter-asset relationships** (e.g., how stocks influence each other), moving beyond single-asset prediction.

                {
                  "action": "Specify the action (`factor` or `model`). Prioritize `hypothesis_specification`; otherwise, decide based on past results.",
                  "hypothesis": "Propose a core, inspirational insight (the 'why', not the 'how'). Must be a single string.\\n- For `factor`: A high-level, conceptual hypothesis about market mechanics, inspired by other domains. NO specific factor details, formulas, or code.\\n- For `model`: A conceptual blueprint describing the model's name, type, and core architecture.",
                  "reason": "Justify the hypothesis. Explain: 1. How it addresses prior findings/limitations. 2. Why this concept/analogy is chosen now. 3. What new insights are expected."
                }
                """
            # ==================================================================
            # END: REVISED MODEL RAG LOGIC
            # ==================================================================

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
                        and not model_inserted
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
                        and not factor_inserted
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