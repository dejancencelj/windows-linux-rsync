import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

import config
import gui_settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory(prefix='sync-settings-'))
        previous = Path.cwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(directory)
        Path('repo/.git').mkdir(parents=True)
        profile = dict(config.DEFAULT_PROFILE, name='First', local_path=str(Path('repo').resolve()),
                       server_host='first.invalid', username='test', remote_path='/srv/first',
                       custom_setting='keep me')
        self.data = {'profiles': [profile, dict(profile, name='Second', server_host='second.invalid')],
                     'active_index': 0, 'custom_option': True}
        config.save_config(self.data)
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(str(exc))
        self.root.withdraw()
        self.dialog = gui_settings.SettingsDialog(self.root)
        self.addCleanup(self.dialog.close)

    def command(self):
        return json.loads(Path('control.json').read_text())['command']

    def test_initial_window_is_disconnected_without_a_command(self):
        self.assertFalse(Path('control.json').exists())
        self.assertEqual(self.dialog.connection_label.cget('text'), 'Disconnected')
        self.assertFalse(self.dialog.connect_button.instate(['disabled']))
        self.assertTrue(self.dialog.disconnect_button.instate(['disabled']))

    def test_connect_saves_selected_profile_and_current_edits(self):
        self.dialog.profile_combo.current(1)
        self.dialog.on_profile_change()
        self.assertEqual(self.command(), 'stop')
        self.dialog.host_var.set('edited.invalid')
        self.dialog.manual_connect()
        saved = config.load_config()
        self.assertEqual(self.command(), 'reconnect')
        self.assertEqual(saved['active_index'], 1)
        self.assertEqual(saved['profiles'][1]['server_host'], 'edited.invalid')
        self.assertEqual(self.dialog.connection_label.cget('text'), 'Connecting…')

    def test_saving_keeps_window_open_and_does_not_connect(self):
        self.dialog.name_var.set('Renamed')
        self.dialog.save()
        saved = config.load_config()
        self.assertEqual(saved['profiles'][0]['name'], 'Renamed')
        self.assertEqual(saved['profiles'][0]['custom_setting'], 'keep me')
        self.assertTrue(saved['custom_option'])
        self.assertFalse(Path('control.json').exists())
        self.assertTrue(self.root.winfo_exists())

    def test_saving_connected_profile_stops_without_reconnecting(self):
        self.dialog.render_status({'connected': True, 'monitoring': True})
        self.dialog.save()
        self.assertEqual(self.command(), 'stop')

    def test_switching_profile_stops_and_does_not_connect(self):
        self.dialog.render_status({'connected': True, 'monitoring': True})
        self.dialog.profile_combo.current(1)
        self.dialog.on_profile_change()
        self.assertEqual(self.command(), 'stop')
        self.assertEqual(config.load_config()['active_index'], 1)

    def test_invalid_port_blocks_connection(self):
        self.dialog.port_var.set('invalid')
        self.dialog.manual_connect()
        self.assertFalse(Path('control.json').exists())
        self.assertIn('SSH port', self.dialog.status_error_label.cget('text'))

    def test_new_and_deleted_profiles_leave_other_profiles_intact(self):
        self.dialog.add_profile()
        self.assertEqual(len(self.dialog.profiles), 3)
        self.assertEqual(self.command(), 'stop')
        self.assertEqual(self.dialog.profiles[0]['name'], 'First')
        with patch('gui_settings.messagebox.askyesno', return_value=True):
            self.dialog.delete_profile()
        self.assertEqual(len(config.load_config()['profiles']), 2)
        self.assertEqual(self.dialog.profiles[0]['name'], 'First')
        self.assertEqual(self.command(), 'stop')

    def test_status_restores_connect_button_after_failure(self):
        self.dialog.render_status({'connecting': True})
        self.assertTrue(self.dialog.connect_button.instate(['disabled']))
        self.dialog.render_status({'error': 'Connection Failed'})
        self.assertFalse(self.dialog.connect_button.instate(['disabled']))
        self.assertEqual(self.dialog.status_error_label.cget('text'), 'Connection Failed')


if __name__ == '__main__':
    unittest.main()
