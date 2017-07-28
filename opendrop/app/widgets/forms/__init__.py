import _settings

from opendrop.app.widgets.utility.package_loader import load as _load
from opendrop.app.widgets.utility.preconfigure import preconfigure \
    as _preconfigure

_contents = _load(_settings)
for k, v in _contents.items():
    globals()[k] = v

def preconfigure(preconfig):
    return _preconfigure(_contents, preconfig)
