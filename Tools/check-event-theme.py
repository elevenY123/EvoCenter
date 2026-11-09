"""Exercise both event boundaries and safe, reversible APT/depiction updates."""
from pathlib import Path
from datetime import timedelta
import importlib.util
import tempfile
import shutil
import hashlib
import gzip
import bz2
import lzma
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_theme', ROOT / 'Tools/event-theme.py')
theme = importlib.util.module_from_spec(spec); spec.loader.exec_module(theme)

def check_index(root):
    raw = (root / 'Packages').read_bytes()
    assert gzip.decompress((root / 'Packages.gz').read_bytes()) == raw
    assert bz2.decompress((root / 'Packages.bz2').read_bytes()) == raw
    assert lzma.decompress((root / 'Packages.xz').read_bytes()) == raw
    section = None
    for line in (root / 'Release').read_text().splitlines():
        if line in ('MD5Sum:', 'SHA1:', 'SHA256:', 'SHA512:'): section = line.rstrip(':').lower().replace('md5sum', 'md5')
        elif section and line.startswith(' '):
            digest, size, file = line.split()
            content = (root / file).read_bytes()
            assert len(content) == int(size)
            assert hashlib.new(section, content).hexdigest() == digest

files = ['Packages', 'Packages.gz', 'Packages.bz2', 'Packages.xz', 'Release', 'Packages-fields.txt',
         'sileo-featured.json', *theme.DEPICTIONS, theme.EVENT + '/normal.json']
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    for file in files:
        (root / file).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / file, root / file)
    # The checkout may itself be in either event state.
    theme.reconcile(root, theme.START - timedelta(seconds=1))
    stock_packages = (root / 'Packages').read_text()
    stock_json = {file: theme.read_json(root / file) for file in theme.DEPICTIONS}
    stock_featured = theme.read_json(root / 'sileo-featured.json')
    assert not theme.reconcile(root, theme.START - timedelta(seconds=1))['changed']
    active = theme.reconcile(root, theme.START)
    assert active['active']
    for record in theme.records((root / 'Packages').read_text()):
        package = theme.field(record, 'Package')
        if package in theme.SLUGS:
            assert theme.field(record, 'Icon') == theme.BASE + theme.SLUGS[package] + '-icon-192.png'
    assert not theme.reconcile(root, theme.START + timedelta(days=1))['changed'], 'Active state must be idempotent'
    check_index(root)
    assert theme.reconcile(root, theme.END - timedelta(microseconds=1))['active']
    restored = theme.reconcile(root, theme.END)
    assert not restored['active']
    assert (root / 'Packages').read_text() == stock_packages, 'Every non-icon package field must survive'
    assert all(theme.read_json(root / file) == data for file, data in stock_json.items())
    assert theme.read_json(root / 'sileo-featured.json') == stock_featured
    assert not theme.reconcile(root, theme.END + timedelta(days=1))['changed']
    check_index(root)
    # A release added during the event and an unrelated depiction edit survive.
    record = theme.records(stock_packages)[0]
    record = theme.replace_field(record, 'Version', theme.field(record, 'Version') + '.future-test')
    (root / 'Packages').write_text(stock_packages + record + '\n\n')
    theme.reconcile(root, theme.START)
    data = theme.read_json(root / 'native.json'); data['futureTest'] = 'Keep this description change'
    theme.save_json(root / 'native.json', data)
    theme.reconcile(root, theme.END)
    assert len(theme.records((root / 'Packages').read_text())) == len(theme.records(stock_packages)) + 1
    assert theme.read_json(root / 'native.json')['futureTest'] == 'Keep this description change'
    assert theme.field(theme.records((root / 'Packages').read_text())[-1], 'Icon') == theme.field(record, 'Icon')
    check_index(root)

normal = theme.read_json(ROOT / theme.EVENT / 'normal.json')
for file, digest in normal['assetSHA256'].items():
    assert hashlib.sha256((ROOT / file).read_bytes()).hexdigest() == digest, ('Original asset changed', file)
for slug in set(theme.SLUGS.values()):
    for file in (slug + '-icon-192.png', slug + '-banner.jpg', slug + '-featured.jpg'):
        assert (ROOT / theme.EVENT / file).is_file()
script = (ROOT / 'site/event-theme.js').read_text()
assert theme.START.isoformat() in script and theme.END.isoformat() in script
assert (theme.END - theme.START).days == 10
print('PASS: exact 10-day window, both boundaries, idempotent apply/restore, new-release preservation, all APT hashes/compressions, 12 untouched originals.')
