"""Tiny local preferences; no account, telemetry or network."""
import json
import os
from pathlib import Path


def default_path():
    if os.name == 'nt':
        folder = Path(os.environ.get('APPDATA',Path.home()/'AppData'/'Roaming'))
    else:
        folder = Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
    return folder/'UniversalTouch'/'settings.json'


class Preferences:
    def __init__(self,path=None):
        self.path = Path(path) if path is not None else default_path()
        self.tutorial_seen = False
        try:
            settings = json.loads(self.path.read_text())
            self.tutorial_seen = (isinstance(settings,dict) and settings.get('tutorial_seen') is True
                                  and settings.get('tutorial_version') == 3)
        except (OSError,ValueError):
            pass

    def accept_tutorial(self):
        self.tutorial_seen = True
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps({'tutorial_seen':True,'tutorial_version':3})+'\n')
        temp.replace(self.path)
