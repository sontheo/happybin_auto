import hashlib
import io
import json
from pathlib import Path
import tempfile
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
            self.assertIsNone(updater.check_update())

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


if __name__ == '__main__':
    unittest.main()
