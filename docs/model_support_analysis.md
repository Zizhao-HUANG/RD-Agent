# RD-Agent Model Support Analysis

This document provides a high-level overview of where and how RD-Agent configures and loads models for Qlib based experiments. It also examines which common model architectures are likely to be supported out of the box.

## A. Configuration File Analysis

Model definitions reside in YAML templates under `rdagent/scenarios/qlib/experiment/`. For example, `model_template/conf_baseline_factors_model.yaml` declares a model section:

```yaml
  task:
      model:
          class: GeneralPTNN
          module_path: qlib.contrib.model.pytorch_general_nn
          kwargs:
              n_epochs: {{ n_epochs }}
              lr: {{ lr }}
              ...
              pt_model_uri: "model.model_cls"
```

The `class` field specifies the Qlib wrapper (`GeneralPTNN`), while `pt_model_uri` points to a `model.py` file containing a `model_cls` variable. Similar patterns appear in `conf_sota_factors_model.yaml` and factor templates.

## B. Python Logic for Model Loading

`QlibModelRunner` in `rdagent/scenarios/qlib/developer/model_runner.py` injects the user supplied `model.py` and executes Qlib with the chosen YAML configuration. The workspace runner calls:

```python
result, stdout = exp.experiment_workspace.execute(
    qlib_config_name="conf_baseline_factors_model.yaml",
    run_env=env_to_use,
)
```

`QlibFBWorkspace.execute()` runs `qrun` with the provided YAML, which imports the model via the `pt_model_uri` path. Therefore any PyTorch module following the `model_cls` convention can be instantiated.

## C. Supported Model Types

Inspecting the installed Qlib package reveals a number of built‑in model modules:

```
['catboost_model', 'double_ensemble', 'gbdt', 'highfreq_gdbt_model', 'linear', 'pytorch_adarnn', 'pytorch_add', 'pytorch_alstm', 'pytorch_alstm_ts', 'pytorch_gats', 'pytorch_gats_ts', 'pytorch_general_nn', 'pytorch_gru', 'pytorch_gru_ts', 'pytorch_hist', 'pytorch_igmtf', 'pytorch_krnn', 'pytorch_localformer', 'pytorch_localformer_ts', 'pytorch_lstm', 'pytorch_lstm_ts', 'pytorch_nn', 'pytorch_sandwich', 'pytorch_sfm', 'pytorch_tabnet', 'pytorch_tcn', 'pytorch_tcn_ts', 'pytorch_tcts', 'pytorch_tra', 'pytorch_transformer', 'pytorch_transformer_ts', 'pytorch_utils', 'tcn', 'xgboost']
```

*(Output truncated for brevity)*

From these module names we can infer native support for the following architectures: **ALSTM, Transformer, LSTM, GRU, TCN, TabNet, SFM,** and **GATs**. They correspond to `pytorch_alstm`, `pytorch_transformer`, `pytorch_lstm`, `pytorch_gru`, `pytorch_tcn`, `pytorch_tabnet`, `pytorch_sfm`, and `pytorch_gats` respectively.

## Conclusion

RD-Agent relies on Qlib's templated YAML configuration and the `model_cls` pattern to load models dynamically. Because Qlib ships with implementations of ALSTM, GRU, LSTM, Transformer, TCN, TabNet, SFM and GATs, these architectures are readily usable within RD-Agent.
