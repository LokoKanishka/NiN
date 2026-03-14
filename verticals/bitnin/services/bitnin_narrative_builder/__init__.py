"""BitNin narrative dataset builder."""

__all__ = ["NarrativeDatasetBuilder"]


def __getattr__(name: str):
    if name == "NarrativeDatasetBuilder":
        from .builder import NarrativeDatasetBuilder

        return NarrativeDatasetBuilder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
