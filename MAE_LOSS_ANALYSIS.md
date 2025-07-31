# MAE Loss 支持分析报告

## 概述

本报告详细分析了在 `conf_sota_factors_model.yaml` 配置文件中使用 MAE (Mean Absolute Error) loss 的可行性。

## 原始配置分析

### 当前配置
```yaml
task:
    model:
        class: GeneralPTNN
        module_path: qlib.contrib.model.pytorch_general_nn
        kwargs:
            loss: mse  # 当前使用MSE loss
```

### 问题发现

通过深入分析 `qlib.contrib.model.pytorch_general_nn.GeneralPTNN` 的源码，发现：

1. **原始GeneralPTNN只支持MSE loss**
   - 在 `loss_fn` 方法中，只检查 `self.loss == "mse"`
   - 如果使用其他loss类型，会抛出 `ValueError("unknown loss")`

2. **源码位置**
   ```python
   # 文件: /home/shenzi/anaconda3/lib/python3.11/site-packages/qlib/contrib/model/pytorch_general_nn.py
   # 行数: 150-160
   
   def loss_fn(self, pred, label, weight=None):
       mask = ~torch.isnan(label)
       if weight is None:
           weight = torch.ones_like(label)
       if self.loss == "mse":
           return self.mse(pred[mask], label[mask], weight[mask])
       raise ValueError("unknown loss `%s`" % self.loss)
   ```

## 解决方案

### 方案1: 使用自定义GeneralPTNN模型

创建了 `CustomGeneralPTNN` 类，扩展原始模型以支持MAE loss：

```python
class CustomGeneralPTNN(GeneralPTNN):
    def mae(self, pred, label, weight):
        loss = weight * torch.abs(pred - label)
        return torch.mean(loss)
    
    def loss_fn(self, pred, label, weight=None):
        # 支持mse和mae两种loss
        if self.loss == "mse":
            return self.mse(pred[mask], label[mask], weight[mask])
        elif self.loss == "mae":
            return self.mae(pred[mask], label[mask], weight[mask])
        else:
            raise ValueError(f"unknown loss `{self.loss}`. Supported losses: 'mse', 'mae'")
```

### 方案2: 使用TRAModel

发现 `qlib.contrib.model.pytorch_tra.TRAModel` 已经支持MAE：

```python
# 在evaluate函数中
def evaluate(pred):
    # ...
    MAE = (diff.abs()).mean()
    return {"MSE": MSE, "MAE": MAE, "IC": IC}
```

## 配置文件修改

### 修改1: 直接修改原始配置
```yaml
# conf_sota_factors_model.yaml
task:
    model:
        kwargs:
            loss: mae  # 改为mae
```
**注意**: 这会导致错误，因为原始GeneralPTNN不支持MAE。

### 修改2: 使用自定义模型
```yaml
# conf_sota_factors_model_mae.yaml
task:
    model:
        class: CustomGeneralPTNN
        module_path: rdagent.scenarios.qlib.experiment.model_template.custom_general_ptnn
        kwargs:
            loss: mae
```

## 技术实现细节

### MAE Loss 实现
```python
def mae_loss(pred, label, weight=None):
    if weight is None:
        weight = torch.ones_like(label)
    loss = weight * torch.abs(pred - label)
    return torch.mean(loss)
```

### 与MSE Loss的对比
- **MSE**: `torch.mean((pred - label) ** 2)`
- **MAE**: `torch.mean(torch.abs(pred - label))`

### 特点对比
| 特性 | MSE | MAE |
|------|-----|-----|
| 对异常值敏感度 | 高（平方惩罚） | 低（线性惩罚） |
| 梯度稳定性 | 可能不稳定 | 更稳定 |
| 收敛速度 | 可能更快 | 可能较慢 |
| 适用场景 | 一般回归 | 对异常值敏感的数据 |

## 测试验证

创建了测试脚本 `test_mae_loss.py` 来验证：

1. **原始GeneralPTNN**: 只支持MSE，MAE会报错
2. **CustomGeneralPTNN**: 支持MSE和MAE
3. **TRAModel**: 支持MAE评估
4. **手动实现**: 验证MAE计算正确性

## 推荐方案

### 短期方案
使用 `CustomGeneralPTNN` 模型，修改配置文件：

```yaml
task:
    model:
        class: CustomGeneralPTNN
        module_path: rdagent.scenarios.qlib.experiment.model_template.custom_general_ptnn
        kwargs:
            loss: mae
```

### 长期方案
1. 向qlib社区贡献MAE loss支持
2. 考虑使用TRAModel作为替代方案
3. 进行A/B测试比较MSE和MAE的性能差异

## 风险与注意事项

1. **兼容性**: 自定义模型需要确保与qlib其他组件的兼容性
2. **性能**: MAE loss可能影响训练收敛速度
3. **维护**: 自定义代码需要长期维护
4. **测试**: 需要充分测试MAE loss在量化投资场景下的效果

## 结论

**是的，可以使用MAE loss**，但需要：

1. 使用自定义的 `CustomGeneralPTNN` 模型
2. 或者切换到支持MAE的 `TRAModel`
3. 进行充分的测试验证

原始配置中的 `loss: mae` 会导致错误，因为 `GeneralPTNN` 只支持MSE loss。 