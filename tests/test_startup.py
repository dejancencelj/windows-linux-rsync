import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, mock_open, patch

import main
import gui_settings


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.app = main.App.__new__(main.App)
        self.app.monitor = None
        self.app.upl = None
        self.app.connected = False
        self.app.connecting = False
        self.app.update_status = Mock()
        self.app.shutdown = Mock()
        self.profile = {
            'name': 'Test', 'local_path': 'missing-folder',
            'server_host': 'example.invalid', 'server_port': 22,
            'username': 'test', 'remote_path': '/test',
        }
        self.app.config_data = {'profiles': [self.profile], 'active_index': 0}
        self.patchers = [
            patch('main.config.load_config', return_value=self.app.config_data),
            patch('main.uploader.Uploader'),
            patch('main.monitor.Monitor'),
            patch('main.os.path.isdir', return_value=True),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ]
        self.mocks = [self.enterContext(patcher) for patcher in self.patchers]
        self.choose_profile = self.enterContext(patch('gui_settings.choose_profile', return_value=0))
        self.save_config = self.enterContext(patch('main.config.save_config'))
        self.command_thread = self.enterContext(patch('main.threading.Thread'))
        self.uploader = self.mocks[1].return_value
        self.monitor = self.mocks[2].return_value

    def test_profile_selection_opens_settings_without_connecting(self):
        self.app.config_data['profiles'].append(dict(
            self.profile, name='Other profile', server_host='selected.invalid'
        ))
        def choose(config_data):
            self.save_config.assert_not_called()
            self.mocks[1].assert_not_called()
            self.command_thread.assert_not_called()
            return 1
        self.choose_profile.side_effect = choose
        with patch('gui_settings.open_settings'):
            self.app.main()
        self.assertEqual(self.app.config_data['active_index'], 1)
        self.save_config.assert_called_once_with(self.app.config_data)
        self.mocks[1].assert_not_called()
        self.command_thread.return_value.start.assert_called_once()
        self.app.shutdown.assert_called_once()

    def test_cancel_does_not_save_or_connect(self):
        self.choose_profile.return_value = None
        with patch('gui_settings.open_settings') as open_settings:
            self.app.main()
        self.save_config.assert_not_called()
        self.mocks[1].assert_not_called()
        self.command_thread.assert_not_called()
        open_settings.assert_not_called()
        self.app.shutdown.assert_called_once()

    def test_missing_folder_is_reported_when_connect_is_requested(self):
        self.mocks[3].return_value = False
        self.app.start_sync()
        self.mocks[1].assert_not_called()
        self.app.update_status.assert_called_with(
            'Local folder does not exist: missing-folder'
        )

    def test_watcher_failure_is_reported_and_resources_are_closed(self):
        self.monitor.start.side_effect = FileNotFoundError('folder disappeared')
        self.monitor.stop.side_effect = RuntimeError('cannot join thread before it is started')
        self.app.start_sync()
        self.uploader.close.assert_called_once()
        self.assertIsNone(self.app.monitor)
        self.assertIsNone(self.app.upl)
        self.assertFalse(self.app.connected)
        self.app.update_status.assert_called_with(
            'Could not start sync: folder disappeared'
        )

    def test_connection_failure_closes_client_and_reports_error(self):
        self.uploader.connect.return_value = False
        self.app.start_sync()
        self.uploader.close.assert_called_once()
        self.mocks[2].assert_not_called()
        self.app.update_status.assert_called_with('Connection Failed')

    def test_successful_start_sets_connected_state(self):
        self.app.start_sync()
        self.monitor.start.assert_called_once()
        self.assertTrue(self.app.connected)
        self.assertIs(self.app.monitor, self.monitor)
        self.app.update_status.assert_called_with()

    def test_old_connection_command_is_discarded_at_startup(self):
        with patch('main.os.path.exists', return_value=True), patch('main.os.remove') as remove:
            with patch('gui_settings.open_settings') as open_settings:
                self.app.main()
        remove.assert_called_once_with('control.json')
        open_settings.assert_called_once_with()
        self.mocks[1].assert_not_called()

    def test_command_listener_keeps_connection_error_visible(self):
        self.uploader.connect.return_value = False
        self.app.running = True
        self.app.update_status = main.App.update_status.__get__(self.app)
        def finish_iteration(_delay):
            self.app.running = False
        with patch('main.os.path.exists', return_value=True), patch('main.os.remove'):
            with patch('builtins.open', mock_open(read_data='{"command": "reconnect"}')):
                with patch('time.sleep', side_effect=finish_iteration), patch('main.update_status_file') as status:
                    self.app.command_loop()
        self.assertEqual(status.call_args.args[2], 'Connection Failed')
        self.assertFalse(status.call_args.args[3])


class ProfileChooserTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(str(exc))
        self.root.withdraw()
        self.addCleanup(self.close_root)
        self.chooser = gui_settings.ProfileChooser(self.root, [
            {'name': 'First', 'local_path': 'C:/first'},
            {'name': 'Second', 'local_path': 'C:/second'},
        ])

    def close_root(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_requires_explicit_selection(self):
        self.assertEqual(self.chooser.profile_combo.current(), -1)
        self.assertTrue(self.chooser.start_button.instate(['disabled']))
        self.chooser.confirm()
        self.assertIsNone(self.chooser.selected_index)
        self.assertTrue(self.root.winfo_exists())

    def test_confirm_returns_selected_profile(self):
        self.chooser.profile_combo.current(1)
        self.chooser.on_profile_change()
        self.assertEqual(self.chooser.folder_label.cget('text'), 'C:/second')
        self.assertFalse(self.chooser.start_button.instate(['disabled']))
        self.chooser.confirm()
        self.assertEqual(self.chooser.selected_index, 1)

    def test_closing_chooser_leaves_selection_unconfirmed(self):
        self.chooser.profile_combo.current(1)
        self.root.destroy()
        self.assertIsNone(self.chooser.selected_index)


@unittest.skipUnless(main.os.name == 'nt', 'Windows batch launcher')
class LauncherTests(unittest.TestCase):
    def test_launcher_uses_its_directory_and_reports_failure(self):
        launcher = Path(main.__file__).with_name('run_app.bat')
        with tempfile.TemporaryDirectory(prefix='sync launcher ') as directory:
            destination = Path(directory)
            shutil.copyfile(launcher, destination / 'run_app.bat')
            for exit_code in (0, 7):
                with self.subTest(exit_code=exit_code):
                    (destination / 'main.py').write_text(
                        'import os, sys\n'
                        'assert os.getcwd() == os.path.dirname(__file__)\n'
                        f'sys.exit({exit_code})\n'
                    )
                    result = subprocess.run(
                        ['cmd.exe', '/d', '/c', str(destination / 'run_app.bat')],
                        cwd=destination.parent, input='\n', capture_output=True,
                        text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, int(exit_code != 0), result.stdout + result.stderr)
                    self.assertIn('Starting Windows-Linux Sync App', result.stdout)
                    self.assertEqual('The app could not start' in result.stdout, exit_code != 0)
                    self.assertNotIn('Installing requirements', result.stdout)


if __name__ == '__main__':
    unittest.main()
