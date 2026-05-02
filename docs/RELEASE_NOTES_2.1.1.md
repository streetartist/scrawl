# Scrawl 2.1.1 版本说明

发布日期：2026-05-02

Scrawl 2.1.1 是一次小版本修复发布，目标很明确：修复 2.1.0 发布后暴露出来的导入问题，并同步完成版本号与发布材料的整理。

## 本次更新重点

### 1. 修复 `scrawl` 导入时的兼容模块错误

2.1.0 发布后，如果直接安装并运行：

```python
from scrawl import *
```

可能会因为 `scrawl_v2.compat` 已删除，但 `scrawl` 包的子模块转发表仍保留 `compat`，从而触发：

- `ModuleNotFoundError: No module named 'scrawl_v2.compat'`

2.1.1 已移除这个过期转发项，修复了官方安装包在导入阶段就失败的问题。

### 2. 版本号统一提升到 2.1.1

本次发布同步更新了以下版本锚点：

- Python 包元数据
- Rust workspace 版本
- `scrawl_v2.__version__`
- 原生模块导出的 `__version__`
- 独立 app 启动日志版本号
- `uv.lock`

这保证 2.1.1 对外版本口径一致，不会出现包版本、原生模块版本和工作区版本不一致的问题。

### 3. 重新生成 `Cargo.lock`

本次发布重新生成了锁文件，使其与当前 2.1.1 工作区状态对齐。

说明：

- 这次 `Cargo.lock` 会带来一批依赖解析结果更新。
- 运行时核心目标不是升级依赖功能，而是保证 lock 文件正确、可解析、可构建。

## 对用户的实际影响

如果你是引擎用户，这次更新意味着：

- 使用官方 PyPI 安装 `scrawl-engine==2.1.1` 后，`from scrawl import *` 不应再因 `compat` 模块缺失而直接崩溃。
- 2.1.0 中已经打通的运行时能力，可以通过 2.1.1 更稳定地被正常导入和使用。

如果你是维护者，这次更新意味着：

- `scrawl` 包和 `scrawl_v2` 包之间的公开转发关系已与当前代码结构重新对齐。
- 2.1.1 是对 2.1.0 的一个发布质量修补版本。

## 安装命令

从官方 PyPI 安装 2.1.1：

```bash
pip install -i https://pypi.org/simple scrawl-engine==2.1.1
```

或者：

```bash
python -m pip install -i https://pypi.org/simple scrawl-engine==2.1.1
```

## 总结

Scrawl 2.1.1 不追求继续扩展 API 面，而是把 2.1.0 发布后发现的关键包导入问题尽快修正，让正式安装、正式导入、正式运行这条路径重新稳定下来。