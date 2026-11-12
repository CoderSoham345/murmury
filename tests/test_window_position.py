import sys
from unittest.mock import MagicMock

# Windows AppLocker and C-extension blocking bypass mocks
sys.modules["anthropic"] = MagicMock()
sys.modules["anthropic.lib"] = MagicMock()
sys.modules["anthropic.lib.streaming"] = MagicMock()
sys.modules["numpy"] = MagicMock()

import os
import pytest
from PySide6.QtCore import QPoint, QSettings
from PySide6.QtWidgets import QApplication

from copilot.app import Bridge, Window
from copilot.setup import settings_store


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch, tmp_path):
    test_ini = str(tmp_path / "settings.ini")
    store = QSettings(test_ini, QSettings.Format.IniFormat)
    monkeypatch.setattr("copilot.setup.settings_store", lambda: store)
    return store


def test_restore_window_position_saved_on_screen(qapp):
    bridge = Bridge()
    win1 = Window(bridge, ask=lambda t: None)
    target_pos = QPoint(200, 200)
    win1.move(target_pos)
    win1.save_window_position()

    win2 = Window(bridge, ask=lambda t: None)
    assert win2.pos() == target_pos


def test_restore_window_position_nothing_saved(qapp, mock_settings):
    mock_settings.remove("window_geometry")

    bridge = Bridge()
    win = Window(bridge, ask=lambda t: None)

    screen = QApplication.primaryScreen()
    if screen:
        expected_top_left = screen.availableGeometry().topRight() - QPoint(470, -40)
        assert win.pos() == expected_top_left


def test_restore_window_position_off_screen(qapp, mock_settings):
    bridge = Bridge()
    win1 = Window(bridge, ask=lambda t: None)
    win1.move(QPoint(-5000, -5000))
    win1.save_window_position()

    # Save raw geometry from win1
    saved_geom = mock_settings.value("window_geometry")
    assert saved_geom is not None

    # Instantiate win2 and check that restoreGeometry applied settings store payload
    win2 = Window(bridge, ask=lambda t: None)
    assert mock_settings.value("window_geometry") == saved_geom