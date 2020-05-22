import os
import shutil
import sublime
from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.settings import ClientConfig, read_client_config
from LSP.plugin.core.logging import debug

CLIENT_SETTING_KEYS = {
    'languages': [],
    'settings': {},
    'env': {
        'LANGSERVER_PROMETHEUSURL': '',
    }
}


def plugin_loaded() -> None:
    LspPromqlPlugin.setup()


class LspPromqlPlugin(LanguageHandler):
    package_name = __package__
    binary_name = 'promql-langserver'
    configuration = {
        'enabled': True,
        'command': [binary_name],
    }

    @classmethod
    def setup(cls) -> None:
        assert cls.package_name
        assert cls.binary_name

    def __init__(self):
        super().__init__()
        assert self.package_name
        self.settings_filename = '{}.sublime-settings'.format(self.package_name)

    @property
    def name(self) -> str:
        return __package__.lower()

    @property
    def config(self) -> ClientConfig:
        settings = {}
        loaded_settings = sublime.load_settings(self.settings_filename)

        if loaded_settings:
            for key, default in CLIENT_SETTING_KEYS.items():
                settings[key] = loaded_settings.get(key, default)

        self.configuration.update(settings)

        return read_client_config(self.name, self.configuration)

    def on_start(self, window) -> bool:
        cmd = self.configuration.get('command', [self.binary_name])[0]
        if shutil.which(cmd) is None:
            sublime.message_dialog(
                "{}: Please install {} for the server to work.".format(self.package_name, cmd))
            return False

        return True
