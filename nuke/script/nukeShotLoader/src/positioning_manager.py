"""
Positioning Manager
Manages node positioning in the Nuke node graph.
"""

from typing import Tuple, List
from .config import Config


class PositioningManager:
    """Manages node positioning in the Nuke graph."""

    def __init__(self, start_x: int = None, start_y: int = None):
        self.start_x = start_x if start_x is not None else Config.START_X
        self.start_y = start_y if start_y is not None else Config.START_Y

        self.current_x = self.start_x

    def get_next_asset_type_position(self) -> Tuple[int, int]:
        """Position for the next asset-type group (current_x, start_y)."""
        return (self.current_x, self.start_y)

    def calculate_backdrop_bounds(
        self,
        nodes: List,
        padding: int = None
    ) -> Tuple[int, int, int, int]:
        """Calculate backdrop bounds (x, y, w, h) to encompass given nodes."""
        if not nodes:
            return (0, 0, 200, 200)

        padding = padding if padding is not None else Config.BACKDROP_PADDING

        min_x = min(n.xpos() for n in nodes)
        max_x = max(n.xpos() + n.screenWidth() for n in nodes)
        min_y = min(n.ypos() for n in nodes)
        max_y = max(n.ypos() + n.screenHeight() for n in nodes)

        xpos = min_x - padding
        ypos = min_y - padding
        bdwidth = (max_x - min_x) + (2 * padding)
        bdheight = (max_y - min_y) + (2 * padding)

        return (xpos, ypos, bdwidth, bdheight)

    def reset(self):
        """Reset to starting position."""
        self.current_x = self.start_x

    def set_anchor(self, x: int, y: int):
        """
        Set the (x, y) anchor used by get_next_asset_type_position(). Allows the
        caller to place each asset-type group at an arbitrary position.
        """
        self.current_x = x
        self.start_y = y
