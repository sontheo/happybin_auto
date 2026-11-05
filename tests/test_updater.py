import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

from modules import updater


class Response(io.BytesIO):
    pass


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as zipped:
        for name, data in files.items():
            zipped.writestr(name, data)
    return stream.getvalue()


class UpdateTests(unittest.TestCase):
    def test_versions_and_release_selection(self):
        self.assertGreater(updater.version_tuple('v4.10.0'), updater.version_tuple('4.9.9'))
        with self.assertRaises(ValueError):
            updater.version_tuple('4.2.0-rc1')
        tag = '4.2.0'
        asset = {'name': updater.ASSET, 'digest': 'sha256:' + 'a' * 64,
                 'browser_download_url': f'https://github.com/sontheo/happybin_auto/releases/download/{tag}/{updater.ASSET}'}
        release = {'tag_name': tag, 'assets': [asset]}
        with patch.object(updater, 'VERSION', '4.1.0'), patch('urllib.request.urlopen', return_value=Response(json.dumps(release).encode())):
            self.assertEqual(updater.check_update()['version'], tag)
        asset['browser_download_url'] = 'https://example.org/file.zip'
        with patch.object(updater, 'VERSION', '4.1.0'), patch('urllib.request.urlopen', return_value=Response(json.dumps(release).encode())):
            with self.assertRaises(updater.UpdateUnavailable):
                updater.check_update()

    def test_stage_validates_digest_and_paths(self):
        payload = archive({'HappybinAuto/HappybinAuto.exe': b'exe', 'HappybinAuto/_internal/a': b'data'})
        release = {'url': 'https://example.org/file.zip', 'digest': hashlib.sha256(payload).hexdigest()}
        with tempfile.TemporaryDirectory() as tmp, patch('tempfile.tempdir', tmp), patch('urllib.request.urlopen', return_value=Response(payload)):
            stage = updater.stage_update(release)
            self.assertTrue((stage / 'HappybinAuto/_internal/a').is_file())
        malicious = archive({'HappybinAuto/../../escape': b'bad'})
        release['digest'] = hashlib.sha256(malicious).hexdigest()
        with tempfile.TemporaryDirectory() as tmp, patch('tempfile.tempdir', tmp), patch('urllib.request.urlopen', return_value=Response(malicious)):
            with self.assertRaises(ValueError):
                updater.stage_update(release)
            self.assertEqual(list(Path(tmp).iterdir()), [])
        release['digest'] = '0' * 64
        with tempfile.TemporaryDirectory() as tmp, patch('tempfile.tempdir', tmp), patch('urllib.request.urlopen', return_value=Response(payload)):
            with self.assertRaises(ValueError):
                updater.stage_update(release)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_stage_reports_download_and_extraction(self):
        payload = archive({'HappybinAuto/HappybinAuto.exe': b'exe', 'HappybinAuto/_internal/a': b'data'})
        release = {'url': 'https://example.org/file.zip', 'digest': hashlib.sha256(payload).hexdigest()}
        response = Response(payload)
        response.headers = {'Content-Length': str(len(payload))}
        events = []
        with tempfile.TemporaryDirectory() as tmp, patch('tempfile.tempdir', tmp), patch('urllib.request.urlopen', return_value=response):
            updater.stage_update(release, progress=lambda *event: events.append(event))
        self.assertEqual(events[0], ('download', len(payload), len(payload)))
        self.assertEqual([event[0] for event in events], ['download', 'verify', 'extract'])

    def test_installer_start_failure_is_reported_before_app_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '_internal').mkdir()
            stage = root / 'stage'
            stage.mkdir()
            with patch.object(updater.sys, 'executable', str(root / 'HappybinAuto.exe')), \
                 patch.object(subprocess, 'CREATE_NO_WINDOW', 0, create=True), \
                 patch.object(subprocess, 'Popen') as popen:
                popen.return_value.poll.return_value = 1
                with self.assertRaisesRegex(RuntimeError, '설치 프로그램을 시작하지 못했습니다'):
                    updater.launch_installer(stage)
                self.assertIn('Bypass', popen.call_args.args[0])

    @unittest.skipUnless(sys.platform == 'win32', 'requires Windows PowerShell')
    def test_installer_replaces_files_after_parent_exits(self):
        with tempfile.TemporaryDirectory(prefix='업데이트 test ') as tmp:
            root = Path(tmp)
            app = root / 'app directory'
            stage = root / 'stage directory'
            (app / '_internal').mkdir(parents=True)
            (stage / 'HappybinAuto' / '_internal').mkdir(parents=True)
            (app / 'HappybinAuto.exe').write_bytes(b'old executable')
            (app / '_internal' / 'old').write_text('old')
            replacement = Path(os.environ['SystemRoot']) / 'System32' / 'where.exe'
            shutil.copyfile(replacement, stage / 'HappybinAuto' / 'HappybinAuto.exe')
            (stage / 'HappybinAuto' / '_internal' / 'new').write_text('new')
            parent = subprocess.Popen(['powershell.exe', '-NoProfile', '-Command', 'Start-Sleep -Seconds 30'],
                                      creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                with patch.object(updater.sys, 'executable', str(app / 'HappybinAuto.exe')), patch.object(updater.os, 'getpid', return_value=parent.pid):
                    installer = updater.launch_installer(stage)
                self.assertEqual((app / 'HappybinAuto.exe').read_bytes(), b'old executable')
                parent.terminate()
                parent.wait(timeout=10)
                installer.wait(timeout=30)
                deadline = time.monotonic() + 30
                while stage.exists() and time.monotonic() < deadline:
                    time.sleep(.1)
                self.assertFalse(stage.exists(), 'installer did not complete')
                self.assertEqual((app / 'HappybinAuto.exe').read_bytes(), replacement.read_bytes())
                self.assertTrue((app / '_internal' / 'new').is_file())
                self.assertFalse((app / '_internal' / 'old').exists())
                deadline = time.monotonic() + 15
                while True:
                    try:
                        (app / 'HappybinAuto.exe').unlink()
                        break
                    except PermissionError:
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(.1)
            finally:
                if parent.poll() is None:
                    parent.terminate()
                    parent.wait(timeout=10)
if __name__ == '__main__':
    unittest.main()
