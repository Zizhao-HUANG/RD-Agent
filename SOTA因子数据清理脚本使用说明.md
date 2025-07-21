# SOTA因子数据清理脚本使用说明

本说明文档介绍了两个用于彻底清理 `rdagent` 项目历史工作区中损坏 SOTA 因子数据（`result.h5`）的脚本：
- `diagnose_final_cleanup.py`：终极诊断脚本，自动识别所有无法正常加载或索引层级不为2的损坏因子文件。
- `delete_corrupted_factors.py`：安全删除脚本，根据诊断结果批量删除所有损坏文件。

---

## 一、适用场景

- 量化平台历史工作区中存在大量 `result.h5` 文件，部分文件因索引层级错误、底层依赖缺失或格式损坏，导致 `rdagent` 工作流报错（如 `AssertionError`、`unrecognized index type` 等）。
- 需要一次性、彻底清理所有无法修复的“僵尸数据”，保证后续流程数据一致性。

---

## 二、脚本说明

### 1. diagnose_final_cleanup.py

- **功能**：递归扫描 `git_ignore_folder/RD-Agent_workspace/` 下所有子目录，尝试加载每个 `result.h5` 文件。
    - 若文件无法被 pandas 正常加载，或索引层级不为2，则视为损坏，输出详细原因和完整路径。
- **输出**：
    - 控制台打印所有损坏文件的路径和原因。
    - 统计总共检查和需删除的文件数。

#### 用法
```bash
python diagnose_final_cleanup.py
```

### 2. delete_corrupted_factors.py

- **功能**：根据 `diagnose_final_cleanup.py` 输出的损坏文件路径，批量删除所有目标文件。
- **配置**：
    - 打开脚本，将所有需删除的文件路径填入 `FILES_TO_DELETE` 列表。
- **输出**：
    - 控制台打印每个文件的删除状态和总计删除数。

#### 用法
```bash
python delete_corrupted_factors.py
```

---

## 三、推荐清理流程

1. **运行诊断脚本**
    - 生成所有损坏文件的完整清单。
    - 复制输出路径，填入删除脚本。
2. **运行删除脚本**
    - 一次性删除所有损坏文件。
3. **再次运行诊断脚本**
    - 确认输出为绿色成功信息：
      `✅ SUCCESS: All checked files are clean and have the correct 2-level index. No corruption found.`

---

## 四、注意事项

- **强烈建议**：删除前备份重要数据，避免误删。
- 脚本仅删除 `FILES_TO_DELETE` 列表中的文件，不会影响其它数据。
- 建议定期运行诊断脚本，及时发现并清理新产生的坏数据。
- 若有新工作区或新因子文件加入，建议重新执行上述流程。

---

## 五、常见问题

- **Q: 删除后还能恢复吗？**
  - A: 脚本为物理删除，无法自动恢复。请提前做好备份。
- **Q: 为什么有些文件无法自动修复？**
  - A: 部分文件损坏严重（如索引类型异常、关键列缺失、底层依赖缺失），只能彻底删除。
- **Q: 诊断脚本报错怎么办？**
  - A: 检查 pandas、h5py、numpy 等依赖是否完整，或直接删除报错文件。

---

## 六、脚本维护与扩展

- 如需扩展支持其它类型的因子文件，只需调整 `TARGET_FILENAME` 变量。
- 如需自动化流程，可将诊断和删除脚本串联，或集成到 CI/CD 流程中。

---

> **作者：AI Cursor & 用户协作**  
> **最后更新：2024-07-21** 