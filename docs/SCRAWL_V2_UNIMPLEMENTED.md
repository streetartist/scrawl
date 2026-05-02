# Scrawl v2 尚未实现项

本文档只记录截至当前仓库状态，仍然没有真正打通到 v2 运行时的能力。

已完成但不再算缺口的项目：

- 广播消息已经通过 Python 命令队列接入运行时。
- `say` / `set_text` 文本显示已经接入运行时。
- 鼠标事件、精灵点击事件、旋转与 mask 点击判定已经接入运行时。
- 音效、背景图、画笔轨迹、精灵颜色同步已经接入运行时。
- `demo_v2/demo_witch_v2.py` 的资源路径已经改成脚本相对路径。

## 仍未实现的核心缺口

### 1. Bridge 启动仍然只消费 Scene 的 sprites

当前 bridge 启动阶段只从 scene 中提取 `sprites`，并在启动系统里生成 sprite 实体。

影响：

- 通用节点树还没有真正进入原生运行时。
- 非 Sprite 类型即使在 Python API 中存在，也不会自动生成原生实体。
- Scene 下的层级结构、复合节点、统一遍历生命周期还没有完整落地。

直接锚点：

- `crates/scrawl-bridge/src/py_game.rs` 中的 `SceneInfo.sprites`
- `crates/scrawl-bridge/src/py_game.rs` 中的 `spawn_sprites_from_python`

### 2. 多个已导出的模块仍未接入原生运行时

Python v2 暴露了较多模块，但 bridge 和独立 app 还没有把它们真正连到运行时插件或实体生成路径。

当前仍需要继续接线的主要模块：

- Physics
- TileMap
- UI
- Particles
- Navigation
- 更完整的 Camera / Light / Path / Node 运行时落地

影响：

- 这些模块的 Python API 可以 import，但实际运行时能力并不完整。
- “能写 API” 与 “能在窗口里正常跑起来” 之间仍有差距。

### 3. 物理对象还没有走通 bridge 实体映射

虽然 v2 暴露了 physics 相关接口，但当前 bridge 启动主要还是按普通 sprite 生成实体，缺少对物理体、碰撞体参数、动力学状态的完整原生映射。

影响：

- 物理属性不能稳定地变成原生世界中的真实物理行为。
- 物理系统与 Python 对象之间还缺统一同步层。

### 4. 原生 API 里还有直接 stub

下面两个原生接口仍是占位实现，不是完整功能：

- `crates/scrawl-bridge/src/py_scene.rs` 的 `broadcast()` 仍然只记录日志。
- `crates/scrawl-bridge/src/py_sprite.rs` 的 `say()` 仍然只记录日志。

说明：

- Python 包装层已经绕过这两个 stub，把常用路径接到了命令队列。
- 但原生 API 本身仍然没有补齐，后续如果直接走 native 层调用，行为仍不完整。

### 5. 独立 app 侧插件装配仍未放开

`crates/scrawl-app/src/main.rs` 里仍有多组插件处于注释状态：

- `ScrawlPhysicsPlugin`
- `ScrawlAudioPlugin`
- `ScrawlAnimationPlugin`
- `ScrawlTilemapPlugin`
- `ScrawlParticlePlugin`
- `ScrawlNavigationPlugin`
- `ScrawlUIPlugin`

影响：

- 独立 app 入口还不能代表“全量功能已装配”的最终状态。
- 即使某些 crate 已存在，实现也还没有进入默认运行组合。

## 建议的后续优先级

1. 先补 bridge 的通用节点/实体生成路径，不再只盯 `scene._sprites`。
2. 再补 physics、tilemap、ui、particles、navigation 这几条真实运行时链路。
3. 最后收尾原生 stub 与独立 app 插件装配，让 API 表面与运行时能力一致。