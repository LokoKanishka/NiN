"""BitNin market dataset builder."""

__all__ = ["MarketDatasetBuilder"]


def __getattr__(name: str):
    if name == "MarketDatasetBuilder":
        from .builder import MarketDatasetBuilder

        return MarketDatasetBuilder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
