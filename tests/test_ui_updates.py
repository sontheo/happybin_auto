"""UI state checks; skipped when Tk or a display is unavailable."""
import tempfile
import time
import unittest
from unittest.mock import patch

try:
    import tkinter as tk
    import ui
except (ImportError, ModuleNotFoundError):
    tk = ui = None


@unittest.skipIf(ui is None, 'Tk or application dependencies unavailable')
class UpdateUiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.app = ui.HappyBeanApp()
        except tk.TclError:
            self.skipTest('no graphical display')
        self.addCleanup(self.app.destroy)
        self.app.update()

    def wait_for(self, state):
        end = time.monotonic() + 3
        while self.app.update_state != state and time.monotonic() < end:
            self.app.update()
            time.sleep(.02)
        self.assertEqual(self.app.update_state, state)

    def test_background_check_states_and_does_not_block_start(self):
        release = {'version': '4.2.0', 'url': 'https://example.test', 'digest': 'a' * 64}
        for result, state, text in [(None, 'current', '최신 버전'), (release, 'available', '업데이트 가능'),
                                    (OSError('offline'), 'error', '확인 실패'),
                                    (ui.updater.UpdateUnavailable(), 'unavailable', '준비 중')]:
            with self.subTest(state=state), patch.object(ui.updater, 'check_update') as check:
                if isinstance(result, Exception):
                    check.side_effect = result
                else:
                    check.return_value = result
                self.app._begin_update_check()
                self.assertEqual(self.app.run_button['state'], 'normal')
                self.wait_for(state)
                self.assertIn(text, self.app.update_status.get())

    def test_ready_update_waits_for_running_automation(self):
        self.app.update_state = 'ready'
        self.app.worker = type('Worker', (), {'is_alive': lambda self: True})()
        with patch.object(ui.sys, 'platform', 'win32'), patch.object(ui.sys, 'frozen', True, create=True), patch.object(ui.messagebox, 'askyesno') as confirm:
            self.app._update_action()
        self.assertIn('수집 종료 후', self.app.update_status.get())
        confirm.assert_not_called()


if __name__ == '__main__':
    unittest.main()
