import pandas as pd
import yaml
from jinja2 import Environment, StrictUndefined
from pathlib import Path
import json

from rdagent.components.runner import CachedRunner
from rdagent.core.conf import RD_AGENT_SETTINGS
from rdagent.core.exception import ModelEmptyError
from rdagent.core.utils import cache_with_pickle
from rdagent.log import rdagent_logger as logger
from rdagent.scenarios.qlib.developer.utils import process_factor_data
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorExperiment
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelExperiment


class QlibModelRunner(CachedRunner[QlibModelExperiment]):
    """
    Docker run
    Everything in a folder
    - config.yaml
    - Pytorch `model.py`
    - results in `mlflow`

    https://github.com/microsoft/qlib/blob/main/qlib/contrib/model/pytorch_nn.py
    - pt_model_uri:  hard-code `model.py:Net` in the config
    - let LLM modify model.py
    """

    def _render_config_template(self, config_path: Path, context: dict) -> dict:
        """
        Render Jinja2 template in YAML config file with given context
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Render the template
            env = Environment(undefined=StrictUndefined)
            template = env.from_string(template_content)
            rendered_content = template.render(**context)
            
            # Parse the rendered YAML
            config = yaml.safe_load(rendered_content)
            logger.info(f"Successfully rendered config template from: {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to render config template {config_path}: {e}")
            raise

    @cache_with_pickle(CachedRunner.get_cache_key, CachedRunner.assign_cached_result)
    def develop(self, exp: QlibModelExperiment) -> QlibModelExperiment:
        if exp.based_experiments and exp.based_experiments[-1].result is None:
            exp.based_experiments[-1] = self.develop(exp.based_experiments[-1])

        exist_sota_factor_exp = False
        if exp.based_experiments:
            SOTA_factor = None
            # Filter and retain only QlibFactorExperiment instances
            sota_factor_experiments_list = [
                base_exp for base_exp in exp.based_experiments if isinstance(base_exp, QlibFactorExperiment)
            ]
            if len(sota_factor_experiments_list) > 1:
                logger.info(f"SOTA factor processing ...")
                SOTA_factor = process_factor_data(sota_factor_experiments_list)

            if SOTA_factor is not None and not SOTA_factor.empty:
                exist_sota_factor_exp = True
                combined_factors = SOTA_factor
                combined_factors = combined_factors.sort_index()
                combined_factors = combined_factors.loc[:, ~combined_factors.columns.duplicated(keep="last")]
                
                # Standardize column index to be robust against pre-existing MultiIndex
                if isinstance(combined_factors.columns, pd.MultiIndex):
                    # If it's already a MultiIndex, flatten it to a single level.
                    # e.g., ('feature', 'ROC20') becomes 'feature_ROC20'
                    logger.info("Detected existing MultiIndex on SOTA factors. Flattening for standardization.")
                    flat_columns = ["_".join(map(str, col)).strip() for col in combined_factors.columns.values]
                else:
                    # If it's a regular index, use it as is.
                    flat_columns = combined_factors.columns

                # Now, reliably create a 2-level MultiIndex from the standardized flat columns.
                new_columns = pd.MultiIndex.from_product([["feature"], flat_columns])
                combined_factors.columns = new_columns
                logger.info(f"Successfully created standardized 2-level MultiIndex for {len(new_columns)} factors.")
                num_features = str(RD_AGENT_SETTINGS.initial_fator_library_size + len(combined_factors.columns))

                target_path = exp.experiment_workspace.workspace_path / "combined_factors_df.parquet"

                # Save the combined factors to the workspace
                combined_factors.to_parquet(target_path, engine="pyarrow")

        if exp.sub_workspace_list[0].file_dict.get("model.py") is None:
            raise ModelEmptyError("model.py is empty")
        # to replace & inject code
        exp.experiment_workspace.inject_files(**{"model.py": exp.sub_workspace_list[0].file_dict["model.py"]})

        env_to_use = {"PYTHONPATH": "./"}

        training_hyperparameters = exp.sub_tasks[0].training_hyperparameters
        # Check if training_hyperparameters is a string, if so, parse it from JSON
        if isinstance(training_hyperparameters, str):
            training_hyperparameters = json.loads(training_hyperparameters)
        if training_hyperparameters:
            env_to_use.update(
                {
                    "n_epochs": str(training_hyperparameters.get("n_epochs", "100")),
                    "lr": str(training_hyperparameters.get("lr", "1e-3")),
                    "early_stop": str(training_hyperparameters.get("early_stop", 10)),
                    "batch_size": str(training_hyperparameters.get("batch_size", 256)),
                    "weight_decay": str(training_hyperparameters.get("weight_decay", 0.0001)),
                }
            )

        logger.info(f"start to run {exp.sub_tasks[0].name} model")
        
        # Determine config file and context
        if exp.sub_tasks[0].model_type == "TimeSeries":
            if exist_sota_factor_exp:
                config_name = "conf_sota_factors_model.yaml"
                env_to_use.update(
                    {"dataset_cls": "TSDatasetH", "num_features": num_features, "step_len": 20}
                )
            else:
                config_name = "conf_baseline_factors_model.yaml"
                env_to_use.update({"dataset_cls": "TSDatasetH", "step_len": 20})
        elif exp.sub_tasks[0].model_type == "Tabular":
            if exist_sota_factor_exp:
                config_name = "conf_sota_factors_model.yaml"
                env_to_use.update({"dataset_cls": "DatasetH", "num_features": num_features})
            else:
                config_name = "conf_baseline_factors_model.yaml"
                env_to_use.update({"dataset_cls": "DatasetH"})
        
        # Load and render config template
        config_path = exp.experiment_workspace.workspace_path / config_name
        if config_path.exists():
            # --- Comprehensive Template Context Creation (Fix for all UndefinedError) ---
            # This block ensures all variables used in YAML templates are provided.
            
            # Sensible defaults based on the high-performance baseline config
            defaults = {
                "n_epochs": 200,
                "lr": 5e-5,
                "early_stop": 20,
                "batch_size": 128,
                "weight_decay": 0.01,
                "d_model": 256,
                "nhead": 8,
                "num_layers": 6,
                "dropout": 0.5,
                "num_timesteps": 480,  # Added the missing variable
                "dataset_cls": "DatasetH",  # Default dataset class
                "step_len": 480,  # Default step length for time series
            }

            template_context = {}
            if training_hyperparameters:
                # If hyperparameters are provided by the LLM, use them
                for key, default_val in defaults.items():
                    template_context[key] = training_hyperparameters.get(key, default_val)
                logger.info(f"Using LLM-provided or default hyperparameters for rendering.")
            else:
                # Otherwise, use the hardcoded defaults
                template_context = defaults.copy()
                logger.info(f"No LLM hyperparameters found. Using hardcoded defaults for rendering.")

            # --- Handle dynamic/context-specific variables ---
            
            # Add num_features to template context (logic from previous successful fix)
            if exist_sota_factor_exp:
                # Use the calculated num_features from SOTA factors
                template_context["num_features"] = int(num_features)
                logger.info(f"Using SOTA factors num_features: {num_features}")
            else:
                # Use default num_features (20 for baseline configuration, as per YAML contract)
                template_context["num_features"] = 20
                logger.info(f"Using default num_features for baseline: 20")
            
            # Override dataset_cls and step_len based on model type
            if exp.sub_tasks[0].model_type == "TimeSeries":
                template_context["dataset_cls"] = "TSDatasetH"
                template_context["step_len"] = 480
                # For time series models, ensure num_timesteps is set
                if "num_timesteps" not in template_context:
                    template_context["num_timesteps"] = 480
            else:  # Tabular
                template_context["dataset_cls"] = "DatasetH"
                # For tabular models, remove step_len as it's not needed
                if "step_len" in template_context:
                    del template_context["step_len"]
            
            logger.info(f"Final template context for rendering: {template_context}")
            
            # Update env_to_use with the correct num_timesteps from template_context
            if "num_timesteps" in template_context:
                env_to_use["num_timesteps"] = str(template_context["num_timesteps"])
                logger.info(f"Updated env_to_use with num_timesteps: {template_context['num_timesteps']}")
            
            # Render the config template
            rendered_config = self._render_config_template(config_path, template_context)
            
            # Write the rendered config back to the workspace
            rendered_config_path = exp.experiment_workspace.workspace_path / f"rendered_{config_name}"
            with open(rendered_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(rendered_config, f, default_flow_style=False, allow_unicode=True)
            
            # Use the rendered config file
            config_name = f"rendered_{config_name}"
            logger.info(f"Using rendered config: {config_name}")
        
        result, stdout = exp.experiment_workspace.execute(
            qlib_config_name=config_name, run_env=env_to_use
        )

        exp.result = result
        exp.stdout = stdout

        if result is None:
            logger.error(f"Failed to run {exp.sub_tasks[0].name}, because {stdout}")
            raise ModelEmptyError(f"Failed to run {exp.sub_tasks[0].name} model, because {stdout}")

        return exp
