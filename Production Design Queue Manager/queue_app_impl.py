"""DesignArrangerGUI shell — methods live in queue_app_gui_setup / queue_app_gui_actions."""

from __future__ import annotations

from queue_app_gui_actions import DesignArrangerGUIActions
from queue_app_gui_setup import DesignArrangerGUISetup


class DesignArrangerGUI(DesignArrangerGUISetup, DesignArrangerGUIActions):
    """Queue App GUI — bootstrap in setup, arrange/process/preview/save in actions."""
