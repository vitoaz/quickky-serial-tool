"""工作区与快捷指令面板回归测试。"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from components.quick_commands_panel_qt import QuickCommandsPanel
from components.work_column_qt import WorkColumn
from components.work_panel_qt import WorkPanel


class WorkPanelAndCommandTests(unittest.TestCase):
    def test_hiding_secondary_column_does_not_permanently_cleanup_tabs(self):
        panel = WorkPanel.__new__(WorkPanel)
        panel.secondary_column = Mock()
        panel.main_column = Mock()
        panel.active_column = panel.secondary_column
        panel.config_manager = Mock()
        panel._update_column_highlight = Mock()

        WorkPanel.toggle_dual_panel_mode(panel, False)

        panel.secondary_column.setVisible.assert_called_once_with(False)
        panel.secondary_column.suspend.assert_called_once()
        panel.secondary_column.cleanup.assert_not_called()
        self.assertIs(panel.active_column, panel.main_column)

    def test_clicking_current_tab_activates_its_column(self):
        column = WorkColumn.__new__(WorkColumn)
        column.on_column_activated = Mock()

        WorkColumn._on_tab_bar_clicked(column, 0)

        column.on_column_activated.assert_called_once_with(column)

    def test_reordering_duplicate_named_groups_keeps_both_groups(self):
        groups = [
            {"name": "重复", "commands": [{"data": "A"}]},
            {"name": "重复", "commands": [{"data": "B"}]},
        ]
        panel = QuickCommandsPanel.__new__(QuickCommandsPanel)
        panel.config_manager = Mock(get_quick_command_groups=Mock(return_value=groups))

        QuickCommandsPanel._save_group_order(panel, 0, 1)

        saved_groups = panel.config_manager.set_quick_command_groups.call_args.args[0]
        self.assertEqual([group["commands"][0]["data"] for group in saved_groups], ["B", "A"])
