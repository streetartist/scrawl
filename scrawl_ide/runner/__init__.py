"""Game runner components.

The imports are intentionally lazy.  ``game_runner`` depends on
``core.i18n`` and eagerly importing it made ``from runner.code_generator``
enter a core/runner cycle during IDE startup and tooling tests.
"""

__all__ = ["GameRunner", "CodeGenerator"]


def __getattr__(name):
    if name == "GameRunner":
        from .game_runner import GameRunner
        return GameRunner
    if name == "CodeGenerator":
        from .code_generator import CodeGenerator
        return CodeGenerator
    raise AttributeError(name)
