"""BitNin episode builder."""

__all__ = ["EpisodeDatasetBuilder"]


def __getattr__(name: str):
    if name == "EpisodeDatasetBuilder":
        from .builder import EpisodeDatasetBuilder

        return EpisodeDatasetBuilder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
