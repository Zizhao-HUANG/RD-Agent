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

        # ==================== [START] DYNAMIC MODEL EXPLORATION LOGIC ====================
        # 架构师注释：这是解决模型迭代瓶颈的核心逻辑。
        # 它通过分析历史实验，动态生成给LLM的指令(RAG)，以在性能停滞时强制探索新模型架构。
        # 该逻辑从 `quant_proposal.py` 中移植并适配，以确保系统行为的一致性。

        # --- 1. 配置项 ---
        # 定义系统支持的所有模型架构，这是探索的宇宙。
        SUPPORTED_MODELS: Set[str] = {"ALSTM", "Transformer", "LSTM", "GRU", "TCN", "TabNet", "SFM", "GATs"}
        # 定义“停滞”的阈值：连续多少次模型迭代失败后触发强制探索。
        STAGNATION_THRESHOLD: int = 3

        # --- 2. 从历史记录中进行状态分析 ---
        consecutive_model_failures = 0
        sota_found_in_history = False
        tried_model_types: Set[str] = set()
        sota_model_type = "N/A"

        # 辅助函数：从实验假设的文本中，不区分大小写地提取模型类型关键字。
        def find_model_type(text: str) -> str:
            for model_name in SUPPORTED_MODELS:
                # 使用正则表达式确保匹配到的是完整的单词，避免 "GRU" 匹配到 "GRU_Attention" 里的 "GRU"
                if re.search(r'\b' + re.escape(model_name) + r'\b', text, re.IGNORECASE):
                    return model_name
            return None

        # 反向遍历历史记录，以找到最后一个模型SOTA，并计算此后的连续失败次数。
        # 注意：这里的 `exp.hypothesis` 来源于 `QlibQuantHypothesis`，它包含 `action` 属性。
        for exp, feedback in reversed(trace.hist):
            # 只关心模型相关的实验
            if hasattr(exp.hypothesis, "action") and exp.hypothesis.action == "model":
                model_type = find_model_type(exp.hypothesis.hypothesis)
                if model_type:
                    tried_model_types.add(model_type)

                if feedback.decision is True:
                    # 找到了最后一个模型SOTA。记录其类型，并停止计算连续失败次数。
                    sota_found_in_history = True
                    sota_model_type = model_type or "Unknown"
                    break 
                elif not sota_found_in_history:
                    # 在找到SOTA之前，遇到的所有失败模型实验都计入连续失败。
                    consecutive_model_failures += 1
        
        # --- 3. 动态生成RAG提示词 ---
        is_stagnated = consecutive_model_failures >= STAGNATION_THRESHOLD

        if is_stagnated:
            # 状态：停滞。生成强指令，强制探索新架构。
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
                # 所有模型都已尝试过。改变策略，要求LLM重新评估与当前SOTA差异最大的模型。
                instruction = (
                    "All available model architectures have been attempted. Your task is to re-evaluate and propose a model that is "
                    f"architecturally most different from the current {sota_model_type}-based SOTA. "
                    "For example, consider Transformer, TabNet, or GATs again, but with a fundamentally new hypothesis about why it might work now (e.g., new factors, different hyperparameters)."
                )

            # 最终的RAG提示词，具有强烈的指令性。
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
            # 状态：未停滞。生成标准的优化提示词，允许在SOTA基础上进行微调或探索相似模型。
            qaunt_rag = f"""
1.  The current SOTA model is based on the **{sota_model_type}** architecture, which has proven effective. You can propose intelligent refinements to its hyperparameters (e.g., hidden size, dropout, learning rate) or minor architectural tweaks (e.g., adding a layer).
2.  You may also consider proposing models with similar inductive biases if you have a strong reason. For example, if GRU is working, LSTM is a reasonable alternative to explore.
3.  The training data consists of less than 1 million samples for the training set and approximately 250,000 samples for the validation set. Please design the hyperparameters accordingly and control the model size. This has a significant impact on the training results.
4.  Focus on a balanced approach: either refine the proven winner or take a small, logical step to a related architecture.
"""
        # ===================== [END] DYNAMIC MODEL EXPLORATION LOGIC =====================


        context_dict = {
            "hypothesis_and_feedback": hypothesis_and_feedback,
            "last_hypothesis_and_feedback": last_hypothesis_and_feedback,
            "SOTA_hypothesis_and_feedback": sota_hypothesis_and_feedback,
            # 使用我们动态生成的RAG提示词替换掉原来的硬编码内容
            "RAG": qaunt_rag,
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
                # 架构师注释：确保这里的历史记录过滤逻辑与新假设生成逻辑兼容
                is_model_action = hasattr(trace.hist[i][0].hypothesis, "action") and trace.hist[i][0].hypothesis.action == "model"
                # 如果没有action属性，我们假设它是一个模型实验（因为这个类是模型专用的）
                if not hasattr(trace.hist[i][0].hypothesis, "action") or is_model_action:
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