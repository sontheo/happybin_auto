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
        self.addCleanup(self.cleanup_app)
        self.app.update()

    def cleanup_app(self):
        for callback in self.app.tk.splitlist(self.app.tk.call('after', 'info')):
            self.app.after_cancel(callback)
        self.app.destroy()

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

    def test_cafe_preset_fills_fields_only_until_saved(self):
        from modules import user_manager
        with tempfile.TemporaryDirectory() as directory, patch.object(user_manager, 'USER_DATA_ROOT', directory):
            self.app.username = 'test-preset'
            problems = []
            def interact():
                try:
                    dialog = next(w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel))
                    entries = [w for w in dialog.winfo_children() if isinstance(w, tk.Entry)]
                    self.app.preset_button.invoke()
                    self.assertEqual([entry.get() for entry in entries], ['31172912', 'https://cafe.naver.com/dpbokji1'])
                    self.assertIsNone(user_manager.load_config('test-preset'))
                    buttons = next(w for w in dialog.winfo_children() if isinstance(w, tk.Frame))
                    next(w for w in buttons.winfo_children() if isinstance(w, ui.RoundedButton) and w._text == '저장').invoke()
                except Exception as exc:
                    problems.append(exc)
                    dialog.destroy()
            self.app.after(50, interact)
            self.app._edit_cafe()
            if problems:
                raise problems[0]
            self.assertEqual(user_manager.load_config('test-preset')['cafe']['id'], 31172912)

    def test_main_controls_fit_in_window(self):
        self.app.update_idletasks()
        for widget in (self.app.run_button, self.app.cancel_button, self.app.cafe_button,
                       self.app.log, self.app.reset_button, self.app.update_button, *self.app.step_rows):
            with self.subTest(widget=widget):
                self.assertGreater(widget.winfo_width(), 1)
                self.assertGreater(widget.winfo_height(), 1)
                self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                     self.app.winfo_rooty() + self.app.winfo_height())

    def test_sections_align_and_show_all_steps(self):
        self.app.update_idletasks()
        steps_bottom = self.app.steps_panel.winfo_rooty() + self.app.steps_panel.winfo_height()
        log_bottom = self.app.log_panel.winfo_rooty() + self.app.log_panel.winfo_height()
        self.assertLessEqual(abs(steps_bottom - log_bottom), 2)
        for row in self.app.step_rows:
            self.assertLessEqual(row.winfo_rooty() + row.winfo_height(), steps_bottom)

    def test_activity_feed_preserves_console_output(self):
        import io
        import queue
        events, console = queue.Queue(), io.StringIO()
        stream = ui._QueueStream(events, console)
        stream.write('[카페] 제목 입력 완료: private text')
        self.assertEqual(events.get_nowait(), ('log', '[카페] 제목 입력 완료: private text'))
        self.assertIn('private text', console.getvalue())
        stream.write('[카페] 등록 완료! 현재 URL: private')
        self.assertEqual(events.get_nowait(), ('log', '[카페] 등록 완료! 현재 URL: private'))
        self.assertEqual(events.get_nowait(), ('activity', '카페 글이 등록되었습니다.'))
        self.app._append_raw_log('first ')
        self.app._append_raw_log('second\nnext')
        self.assertEqual(self.app.log.get('1.0', 'end-1c'), 'first second\nnext')
        self.app._show_progress('failed', 'private diagnostic')
        self.app._finish({})
        self.assertEqual(self.app.live_text.cget('text'), '오류')
        self.assertNotIn('private diagnostic', self.app.log.get('1.0', 'end'))

    def test_worker_sends_stdout_and_stderr_to_activity_log(self):
        import sys
        def fake_run(username, progress, cancel):
            print('first line')
            print('error detail', file=sys.stderr)
            progress('complete', 'summary')
            return {}
        with patch.object(ui, 'run_automation', fake_run):
            self.app._start()
            end = time.monotonic() + 3
            while self.app.run_button['state'] == 'disabled' and time.monotonic() < end:
                self.app.update()
                time.sleep(.02)
        output = self.app.log.get('1.0', 'end')
        self.assertIn('first line\n', output)
        self.assertIn('error detail\n', output)
        self.assertEqual(self.app.run_button['state'], 'normal')

    def test_ready_update_waits_for_running_automation(self):
        self.app.update_state = 'ready'
        self.app.worker = type('Worker', (), {'is_alive': lambda self: True})()
        with patch.object(ui.sys, 'platform', 'win32'), patch.object(ui.sys, 'frozen', True, create=True), patch.object(ui.messagebox, 'askyesno') as confirm:
            self.app._update_action()
        self.assertIn('수집 종료 후', self.app.update_status.get())
        confirm.assert_not_called()


if __name__ == '__main__':
    unittest.main()
