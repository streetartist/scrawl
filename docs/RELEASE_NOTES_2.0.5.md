# Scrawl 2.0.5 版本说明

发布日期：2026-05-02

Scrawl 2.0.5 是一次面向正式版本发布的重要升级。本次更新将原本分散在 `scrawl_v2` 下的能力提升为正式版本能力，补齐了大量 2D 游戏开发常用模块，同时显著扩展了 IDE 对新节点体系与可视化编辑的支持。

本版本的核心目标有三点：

1. 将 Scrawl 2.x 作为正式发布版本对外提供。
2. 建立统一、可发布的 Python + Rust 打包链路。
3. 让 IDE 能直接使用新一代节点与运行时 API 进行开发。

## 版本亮点

### 1. Scrawl 2.x 正式化

- 正式提供 `scrawl` 作为主导入入口。
- 保留 `scrawl_v2` 作为兼容导入层，方便旧代码逐步迁移。
- Python 包元数据已切换到 2.0.5 正式版本。
- Rust 工作区版本同步提升到 2.0.5。
- Native 模块目标已统一到 `scrawl.scrawl_native`。

### 2. 新一代运行时 API 大幅扩展

本次新增或完善了以下核心模块：

- 节点系统：`Node`、`Node2D`
- 数学工具：`Vector2`、`Rect2`、`Transform2D`、`Color`
- 动画系统：`AnimatedSprite2D`、`AnimationPlayer`、`Tween`
- 物理系统：`StaticBody2D`、`RigidBody2D`、`KinematicBody2D`、`Area2D`、`CollisionShape2D`
- 摄像机：`Camera2D`
- 音频系统：`AudioPlayer`、`AudioPlayer2D`、`AudioManager`
- 瓦片地图：`TileMap`、`TileSet`、`TileMapLayer`
- 粒子系统：`ParticleEmitter2D`
- 寻路导航：`NavigationGrid`、`NavigationAgent2D`
- UI 系统：`Label`、`Button`、`ProgressBar`、`Panel`、`CanvasLayer`
- 光照系统：`PointLight2D`、`DirectionalLight2D`
- 路径系统：`Path2D`、`PathFollow2D`、`Line2D`
- 状态机：`State`、`StateMachine`
- 信号系统：`Signal`
- 资源管理：`ResourceLoader`
- 输入映射：`Input`、`InputMap`
- 计时器：`Timer`

### 3. IDE 节点编辑能力显著增强

Scrawl IDE 现已支持更完整的节点化工作流：

- 支持从场景中直接添加不同类型节点，而不再局限于传统 Sprite。
- 节点树显示更丰富的节点类型与图标。
- 属性面板新增针对不同节点类型的专用配置区。
- 代码生成器已切换为使用正式 `scrawl` 包导入。
- 运行器已调整 `PYTHONPATH` 处理方式，以兼容新的包布局。

### 4. 新增多个可视化编辑器

IDE 本次新增了多种面向内容生产的可视化编辑工具：

- TileMap 编辑器
- SpriteFrames 动画帧编辑器
- Path 路径编辑器
- Navigation Grid 导航网格编辑器

这使得地图、动画、路径和寻路数据不再需要完全依赖手写代码维护。

### 5. AI 与代码片段同步升级

- AI 生成提示词已更新，更贴合 `scrawl_v2` / `scrawl` 新 API。
- 代码片段库新增大量 2.x API 示例。
- 输入检测、音频、动画、UI、物理、导航、资源管理等片段得到补充。

### 6. 文档体系补全

- 新增完整手册：Scrawl IDE 与 Scrawl 2.x 使用说明。
- 补充了节点系统、API 参考、专用编辑器、项目结构与已知限制等内容。
- 提供了 Markdown 与 PDF 两种手册形式。

## 打包与发布改进

本版本还完成了正式发布链的整理：

- GitHub Actions 发布流程已切换到基于 `maturin` 的构建与发布方式。
- `setup.py` 已改为显式阻止旧 setuptools 打包路径，避免误发旧版元数据。
- Python 打包信息已统一到 `pyproject.toml`。

这意味着后续 2.x 版本将沿用新的正式发布链路，而不再依赖旧的 0.x 打包方式。

## 迁移说明

### 新项目推荐写法

推荐直接使用：

```python
from scrawl import *
```

### 兼容旧版 2.x 试验代码

旧代码如果仍使用：

```python
from scrawl_v2 import *
```

当前仍可继续运行，但建议逐步迁移到 `scrawl` 入口，以便后续版本保持一致。

## 对用户的实际影响

如果你是引擎用户，这次更新意味着：

- 可以开始按正式 2.x 版本理解和使用 Scrawl。
- 可用 API 面大幅提升，能够覆盖更多 Godot 风格 2D 游戏开发场景。
- 使用 IDE 时，可直接创建更多节点类型并通过可视化界面编辑。
- 项目代码生成将默认走新的 `scrawl` 官方入口。

如果你是维护者或发布者，这次更新意味着：

- 2.0.5 的包结构、版本号和发布链已经基本统一。
- 后续发布应基于 `pyproject.toml + maturin` 路线继续维护。

## 已知事项

- 本地完整构建仍依赖 Rust 环境与相关构建条件。
- 某些新模块当前更偏向数据模型与 API 框架完善，具体渲染或运行时能力仍可继续增强。
- 若本地或 CI 环境网络不稳定，推送与发布流程可能受外部网络影响。

## 总结

Scrawl 2.0.5 标志着项目从试验性 `scrawl_v2` 结构迈向正式发布形态，同时把运行时能力、IDE 节点工作流、文档和发布链一起推进到了新的阶段。

这是一次真正意义上的基础设施升级，也是后续 2.x 迭代的起点。