import os
import logging
from os.path import join

from .production import defaults as production_defaults

# These directories are in Appdata (e.g. C:\ProgramData on some Win7 versions)
if 'ALLUSERSPROFILE' in os.environ:
    APPDATA_DIR = os.path.join(os.environ['ALLUSERSPROFILE'], "FAForeverDevelop")
else:
    APPDATA_DIR = os.path.join(os.environ['HOME'], "FAForeverDevelop")

defaults = production_defaults.copy()
defaults['host'] = 'vmrbg145.informatik.tu-muenchen.de'
defaults['lobby/host'] = 'vmrbg145.informatik.tu-muenchen.de'
defaults['chat/host'] = 'vmrbg145.informatik.tu-muenchen.de'
defaults['content/host'] = 'http://vmrbg145.informatik.tu-muenchen.de'
defaults['updater/gh_release_url'] = 'https://api.github.com/repos/muellni/client/releases?per_page=20'
defaults['client/logs/console'] = True
defaults['client/data_path'] = APPDATA_DIR
defaults['client/logs/path'] = join(APPDATA_DIR, 'logs')
defaults['game/bin/path'] = join(APPDATA_DIR, 'bin')
defaults['game/engine/path'] = join(join(APPDATA_DIR, 'repo'), 'binary-patch')
defaults['game/logs/path'] = join(APPDATA_DIR, 'logs')
defaults['game/mods/path'] = join(join(APPDATA_DIR, 'repo'), 'mods')
defaults['game/maps/path'] = join(join(APPDATA_DIR, 'repo'), 'maps')
