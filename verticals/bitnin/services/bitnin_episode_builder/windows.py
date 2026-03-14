from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EpisodeWindow:
    pre_start_index: int
    event_start_index: int
    event_end_index: int
    post_end_index: int


def build_episode_window(
    *,
    total_bars: int,
    trigger_index: int,
    pre_bars: int = 3,
    event_bars: int = 1,
    post_bars: int = 7,
) -> EpisodeWindow:
    event_start = max(0, trigger_index)
    event_end = min(total_bars - 1, trigger_index + event_bars - 1)
    pre_start = max(0, event_start - pre_bars)
    post_end = min(total_bars - 1, event_end + post_bars)
    return EpisodeWindow(
        pre_start_index=pre_start,
        event_start_index=event_start,
        event_end_index=event_end,
        post_end_index=post_end,
    )
