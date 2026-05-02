# Scrawl 2.1.2 版本说明

发布日期：2026-05-02

Scrawl 2.1.2 是一次补丁修复发布，重点处理 2.1.1 中图片精灵被错误染色的问题。

## 本次更新重点

### 修复图片 costume 精灵被默认颜色错误 tint

在 2.1.1 中，Python 层的 `Sprite` 默认带有颜色值 `(255, 100, 100)`。

这个默认值本来只应该影响没有 costume 图片的纯色精灵，但运行时在每帧同步颜色时，没有区分“图片精灵”和“纯色形状精灵”，导致带有 SVG 或 PNG costume 的精灵也会被额外着色。

这会直接表现为：

- 女巫等使用原始美术资源的角色颜色失真
- costume 图像整体偏红或被意外染色

2.1.2 已修复这条同步链路：

- 有图片 costume 的精灵保持原始贴图颜色，不再应用默认 tint
- 无图片 costume 的默认形状精灵仍然保留 `color` 属性驱动的外观行为

## 对用户的实际影响

- `demo_v2/demo_witch_v2.py` 中的女巫、美术资源类敌人和其他图片精灵颜色会恢复正常
- 旧有依赖 `Sprite.color` 的纯色默认形状行为不会被破坏

## 安装命令

从官方 PyPI 安装 2.1.2：

```bash
pip install -i https://pypi.org/simple scrawl-engine==2.1.2
```

或者：

```bash
python -m pip install -i https://pypi.org/simple scrawl-engine==2.1.2
```

## 总结

Scrawl 2.1.2 解决的是运行时颜色同步规则本身，而不是对某个 demo 的临时补丁，因此这次修复会作用到所有使用 costume 图像的精灵。