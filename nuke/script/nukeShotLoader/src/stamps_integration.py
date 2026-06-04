"""
Stamps Integration
Integration with Stamps module for creating postage stamps.
Adapted from nukeMultiShotSetup render_loader.py
"""

import os
import sys
from .config import Config


# Try to import Stamps module
STAMPS_AVAILABLE = False
stamps_module = None


def _try_import_stamps():
    """Attempt to import Stamps module from various locations."""
    global STAMPS_AVAILABLE, stamps_module

    if not Config.ENABLE_STAMPS:
        print("[StampsIntegration] Stamps integration disabled in config")
        return False

    try:
        # Try accessing from nuke.thisNode() context (most reliable in Nuke)
        if 'stamps' in sys.modules:
            stamps_module = sys.modules['stamps']
            STAMPS_AVAILABLE = True
            print("[StampsIntegration] Stamps loaded from sys.modules")
            return True
    except:
        pass

    try:
        # Try direct import
        from stamps import stamps as stamps_module_import
        stamps_module = stamps_module_import
        STAMPS_AVAILABLE = True
        print("[StampsIntegration] Stamps imported directly")
        return True
    except ImportError:
        pass

    # Try searching in known paths
    for stamps_path in Config.STAMPS_PATHS:
        if os.path.exists(stamps_path):
            try:
                if stamps_path not in sys.path:
                    sys.path.insert(0, stamps_path)
                import stamps as stamps_module_import
                stamps_module = stamps_module_import
                STAMPS_AVAILABLE = True
                print(f"[StampsIntegration] Stamps loaded from {stamps_path}")
                return True
            except ImportError:
                continue

    print("[StampsIntegration] Stamps module not found - stamp creation will be skipped")
    return False


# Try to import on module load
_try_import_stamps()


class StampsIntegration:
    """Integration with Stamps module for creating postage stamps."""

    def __init__(self):
        """Initialize Stamps integration."""
        self.available = STAMPS_AVAILABLE
        self.stamps = stamps_module

    def is_available(self) -> bool:
        """Check if Stamps is available."""
        return self.available

    def create_anchor_stamp(self, source_node, name: str = None, y_offset: int = 150):
        """
        Create an Anchor Stamp from a source node.

        Stamps creates anchors from the currently selected node in Nuke,
        so we need to temporarily select the source_node.

        Args:
            source_node: Nuke node to create anchor from
            name (str): Optional title for the stamp
            y_offset (int): Vertical gap (px) between the source node's ypos
                and the anchor. Caller can shrink this when the chain is
                already padded (e.g. an ILGC_ReadCleanup sits above).

        Returns:
            Anchor node or None if Stamps not available
        """
        if not self.available or self.stamps is None:
            print("[StampsIntegration] Cannot create anchor: Stamps not available")
            return None

        try:
            import nuke

            # Save current selection
            original_selection = nuke.selectedNodes()

            # Deselect all nodes
            for n in original_selection:
                n.setSelected(False)

            # Select the source node (Stamps uses Nuke's selection)
            source_node.setSelected(True)

            # Create anchor with title parameter (stamps.anchor expects title as first param)
            title = name if name else source_node.name()
            anchor = self.stamps.anchor(title=title)

            # Connect the anchor to the source node
            # The anchor is created without any input connection by default
            anchor.setInput(0, source_node)

            # Center the anchor horizontally under the source node. Aligning by
            # xpos alone leaves a visible offset whenever the source and the
            # anchor have different widths (e.g. Camera4 vs anchor stamp).
            source_center_x = source_node.xpos() + source_node.screenWidth() / 2
            anchor_x = int(source_center_x - anchor.screenWidth() / 2)
            anchor.setXYpos(anchor_x, source_node.ypos() + y_offset)

            # Restore original selection
            source_node.setSelected(False)
            for n in original_selection:
                n.setSelected(True)

            print(f"[StampsIntegration] Created anchor stamp: {title} (connected to {source_node.name()})")
            return anchor

        except Exception as e:
            print(f"[StampsIntegration] Error creating anchor stamp: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_wired_stamp(self, anchor_node, position: tuple = None):
        """
        Create a Wired Stamp connected to an Anchor.

        Args:
            anchor_node: Anchor node to connect to
            position (tuple): Optional (x, y) position

        Returns:
            Wired stamp node or None if Stamps not available
        """
        if not self.available or self.stamps is None:
            print("[StampsIntegration] Cannot create wired stamp: Stamps not available")
            return None

        try:
            import nuke

            # Save current selection and deselect all nodes
            # This is critical for stamps.wired() to work correctly
            original_selection = nuke.selectedNodes()
            for n in original_selection:
                n.setSelected(False)

            # Create wired stamp using Stamps module
            # stamps.wired() expects the anchor as parameter
            if hasattr(self.stamps, 'wired'):
                wired = self.stamps.wired(anchor=anchor_node)

                if wired:
                    # Center the wired horizontally under the anchor — the
                    # caller's position[0] is ignored because anchor and wired
                    # can have different widths, which would offset xpos-only
                    # alignment. Only the y from `position` is honoured.
                    if position:
                        anchor_center_x = anchor_node.xpos() + anchor_node.screenWidth() / 2
                        wired_x = int(anchor_center_x - wired.screenWidth() / 2)
                        wired.setXYpos(wired_x, position[1])

                    # Restore original selection (excluding anchor)
                    for n in original_selection:
                        n.setSelected(True)

                    print(f"[StampsIntegration] Created wired stamp: {wired.name()}")
                    return wired
                else:
                    # Restore selection even if wired creation failed
                    for n in original_selection:
                        n.setSelected(True)
                    print("[StampsIntegration] stamps.wired() returned None")
                    return None
            else:
                # Restore selection
                for n in original_selection:
                    n.setSelected(True)
                print("[StampsIntegration] Stamps module missing 'wired' function")
                return None

        except Exception as e:
            print(f"[StampsIntegration] Error creating wired stamp: {e}")
            import traceback
            traceback.print_exc()
            return None

# Global instance
stamps_integration = StampsIntegration()


def get_stamps_integration() -> StampsIntegration:
    """Get the global Stamps integration instance."""
    return stamps_integration
