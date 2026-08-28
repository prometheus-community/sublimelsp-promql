import hashlib
import os
import shutil
import sublime
import tarfile
from threading import Thread
from urllib.request import FancyURLopener
from sublime_lib import ActivityIndicator
from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.settings import ClientConfig, read_client_config
from LSP.plugin.core.logging import debug

BINARY_NAME = 'promql-langserver'
DOWNLOADS = {
    'windows': {
        'x64': {
            'url': 'https://github.com/prometheus-community/promql-langserver/releases/download/v0.5.1/promql-langserver_0.5.1_windows_amd64.tar.gz',
            'checksum': 'bf6bfe096acce1ac920c21bedc7408ed9f51f97921a1c1d20a7eecd17a14331d',
        },
    },
    'osx': {
        'x64': {
            'url': 'https://github.com/prometheus-community/promql-langserver/releases/download/v0.5.1/promql-langserver_0.5.1_darwin_amd64.tar.gz',
            'checksum': 'f5c000c9f3df70d9d0867c404a3a8b0e18253578dd9eb25c4cbbb9ee9ab04631',
        }
    },
    'linux': {
        'x64': {
            'url': 'https://github.com/prometheus-community/promql-langserver/releases/download/v0.5.1/promql-langserver_0.5.1_linux_amd64.tar.gz',
            'checksum': '55d3195b023062463448491ea071d66f6d5e33bf0a676f9b346a0b15192b0687',
        },
    },
}

def plugin_loaded() -> None:
    LspPromqlPlugin.setup()


def checksum_verified(expected, filepath) -> bool:
    sha256_hash = hashlib.sha256()

    with open(filepath, "rb") as f:
        # Update hash string value in blocks of 4K.
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)

        digest = sha256_hash.hexdigest()
        return expected == digest


class ServerResource:
    def __init__(self):
        self._ready = False
        self._require_download = False
        self._executable = None

    # this is called before setup()
    def config(self, executable) -> str:
        self._executable = executable
        if os.sep in executable:
            self._ready = os.path.isfile(executable)
        elif shutil.which(executable):
            self._ready = True
        else:
            self._cache_path = os.path.join(sublime.cache_path(), __package__)
            os.makedirs(self._cache_path, exist_ok=True)
            self._executable = os.path.join(self._cache_path, executable)

            if os.path.isfile(self._executable):
                self._ready = True
            else:
                self._ready = False
                self._require_download = True

        return self._executable


    def setup(self) -> None:
        if self._require_download:
            self.download_server()

    def cleanup(self) -> None:
        if os.path.isdir(self._cache_path):
            shutil.rmtree(self._cache_path)

    def download_server(self) -> None:
        platform = sublime.platform()
        arch = sublime.arch()
        info = DOWNLOADS.get(platform).get(arch)
        if info:
            url = info.get('url')
            checksum = info.get('checksum')

            def _download() -> None:
                debug('Downloading server from', url)
                target = sublime.active_window()
                label = 'Downloading PromQL language server'

                with ActivityIndicator(target, label):
                    try:
                        opener = FancyURLopener()
                        tmp_file, _ = opener.retrieve(url)

                        if not checksum_verified(checksum, tmp_file):
                            debug('Checksum error.')
                            sublime.status_message('Server binary', os.path.basename(tmp_file), 'checkusm error.')
                            return

                        # extract and copy the cache
                        with tarfile.open(tmp_file) as tf:
                            def is_within_directory(directory, target):
                                
                                abs_directory = os.path.abspath(directory)
                                abs_target = os.path.abspath(target)
                            
                                prefix = os.path.commonprefix([abs_directory, abs_target])
                                
                                return prefix == abs_directory
                            
                            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                            
                                for member in tar.getmembers():
                                    member_path = os.path.join(path, member.name)
                                    if not is_within_directory(path, member_path):
                                        raise Exception("Attempted Path Traversal in Tar File")
                            
                                tar.extractall(path, members, numeric_owner=numeric_owner) 
                                
                            
                            safe_extract(tf, self._cache_path)

                        os.unlink(tmp_file)

                        self._ready = True
                    except Exception as ex:
                        debug('Failed downloading server:', ex)
                    finally:
                        opener.close()

            thread = Thread(target=_download)
            thread.start()


    @property
    def ready(self) -> bool:
        return self._ready


class LspPromqlPlugin(LanguageHandler):
    DEFAULT_SETTINGS = {
        'languages': [],
        'settings': {},
        'env': {
            'LANGSERVER_PROMETHEUSURL': '',
        },
    }
    __server = ServerResource()

    @classmethod
    def setup(cls) -> None:
        if cls.__server.ready:
            return
        else:
            cls.__server.setup()

    @classmethod
    def cleanup(cls) -> None:
        cls.__server.cleanup()

    def __init__(self):
        super().__init__()
        self.configuration = {
            'enabled': True,
            'command': [BINARY_NAME],
        }
        self.settings_filename = '{}.sublime-settings'.format(__package__)

    @property
    def name(self) -> str:
        return __package__.lower()

    @property
    def config(self) -> ClientConfig:
        settings = {}
        loaded_settings = sublime.load_settings(self.settings_filename)

        if loaded_settings:
            for key, default in self.DEFAULT_SETTINGS.items():
                settings[key] = loaded_settings.get(key, default)

        self.configuration.update(settings)
        executable = self.__server.config(self.configuration.get('command')[0])
        self.configuration.update({'command': [executable]})

        debug(__package__, 'read config:', self.configuration)
        return read_client_config(self.name, self.configuration)

    def on_start(self, window) -> bool:
        if not self.__server.ready:
            cmd = self.configuration.get('command')[0]
            debug(__package__, 'command', cmd, 'is not ready')
            sublime.status_message(
                "{}: Please install {} for the server to work.".format(__package__, cmd))
            return False

        return True
