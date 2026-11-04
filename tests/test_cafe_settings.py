import os
import tempfile
import unittest
from unittest.mock import patch

import config
from modules import bean_banner, user_manager


class CafeSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = patch.object(user_manager, 'USER_DATA_ROOT', self.tmp.name)
        self.root.start()
        self.original = (config.CAFE_ID, config.CAFE_URL, config.CAFE_WRITE_URL)
        self.addCleanup(self.restore)

    def restore(self):
        config.CAFE_ID, config.CAFE_URL, config.CAFE_WRITE_URL = self.original
        self.root.stop()
        self.tmp.cleanup()

    def test_validation(self):
        self.assertEqual(config.validate_cafe('', ''), (0, ''))
        self.assertEqual(config.validate_cafe('123', 'https://cafe.naver.com/example/'), (123, 'https://cafe.naver.com/example'))
        for cafe_id, url in [('abc', 'https://cafe.naver.com/example'), ('123', 'https://evil.example/example'),
                             ('123', 'https://cafe.naver.com/ca-fe/cafes/456'), ('123', '')]:
            with self.subTest(cafe_id=cafe_id, url=url), self.assertRaises(ValueError):
                config.validate_cafe(cafe_id, url)

    def test_saved_destination_applies_to_writes_and_banners(self):
        user_manager.save_config({'user_name': 'test', 'cafe': {'id': 123, 'url': 'https://cafe.naver.com/example'}}, 'test')
        config.apply_cafe_for_user('test')
        self.assertIn('/123/articles/write', config.CAFE_WRITE_URL)
        with patch.object(bean_banner, 'scan_page_for_bean_banner', return_value={'exists': False, 'clickable': False, 'clicked': False, 'page_name': 'test'}) as scan:
            bean_banner.scan_all_bean_banners(None)
        self.assertIn(('https://cafe.naver.com/example', '카페_메인'), [(call.args[1], call.args[2]) for call in scan.call_args_list])
        user_manager.save_config({'cafe': {'id': 0, 'url': ''}}, 'test')
        config.apply_cafe_for_user('test')
        self.assertEqual(config.CAFE_WRITE_URL, '')
        with patch.object(bean_banner, 'scan_page_for_bean_banner', return_value={'exists': False, 'clickable': False, 'clicked': False, 'page_name': 'test'}) as scan:
            bean_banner.scan_all_bean_banners(None)
        self.assertNotIn('카페_메인', [call.args[2] for call in scan.call_args_list])

    def test_environment_default_survives_other_users_override(self):
        with patch.object(config, 'DEFAULT_CAFE_ID', 456), patch.object(config, 'DEFAULT_CAFE_URL', 'https://cafe.naver.com/default'):
            user_manager.save_config({'cafe': {'id': 123, 'url': 'https://cafe.naver.com/example'}}, 'test')
            config.apply_cafe_for_user('test')
            config.apply_cafe_for_user('another')
            self.assertEqual((config.CAFE_ID, config.CAFE_URL), (456, 'https://cafe.naver.com/default'))


if __name__ == '__main__':
    unittest.main()
