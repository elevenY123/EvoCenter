"""Time-box the GTA VI store artwork without touching any DEB or runtime code.

The browser uses the same absolute interval in event-theme.js. This reconciler
only owns package Icon fields and depiction/featured artwork fields, so later
package releases and changes to descriptions are retained when the event ends.
"""
from pathlib import Path
from datetime import datetime, timezone
from email.utils import format_datetime
import argparse
import bz2
import gzip
import hashlib
import json
import lzma
import re

START = datetime.fromisoformat('2026-11-10T00:00:00+08:00')
END = datetime.fromisoformat('2026-11-20T00:00:00+08:00')
EVENT = 'site/events/gta6-2026'
BASE = 'https://eleveny123.github.io/' + EVENT + '/'
SLUGS = {'com.jaysuen.evocenter': 'evocenter', 'com.jaysuen.evocenter.arm64': 'evocenter',
         'com.jaysuen.artmotion': 'artmotion', 'com.jaysuen.artmotion.legacy': 'artmotion',
         'dev.islandglass.tweak': 'islandblur', 'dev.islandblur.arm64': 'islandblur'}
DEPICTIONS = {'native.json': 'evocenter', 'native-legacy.json': 'evocenter',
              'ArtMotion/native.json': 'artmotion', 'ArtMotion/native-legacy.json': 'artmotion',
              'ArtMotion/native.en.json': 'artmotion', 'ArtMotion/native-legacy.en.json': 'artmotion',
              'IslandBlur/native.json': 'islandblur'}
NORMAL_ASSETS = ['assets/icon.png', 'assets/banner.png', 'ArtMotion/assets/icon.png',
                 'ArtMotion/assets/banner.png', 'ArtMotion/assets/featured.png',
                 'IslandBlur/assets/icon.png', 'IslandBlur/assets/banner.png',
                 'site/icons/evocenter.png', 'site/icons/artmotion.png', 'site/icons/islandblur.png',
                 'CydiaIcon.png', 'SileoIcon.png']

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode())

def records(text):
    return text.strip().split('\n\n')

def field(record, key):
    match = re.search(r'^' + re.escape(key) + r': (.*)$', record, re.M)
    return match.group(1) if match else None

def identity(record):
    return '|'.join(field(record, key) or '' for key in ('Package', 'Version', 'Architecture', 'Filename'))

def replace_field(record, key, value):
    if value is None:
        return re.sub(r'^' + re.escape(key) + r':.*\n?', '', record, flags=re.M).rstrip('\n')
    line = key + ': ' + value
    return re.sub(r'^' + re.escape(key) + r':.*$', lambda _: line, record, flags=re.M) if field(record, key) is not None else record + '\n' + line

def initialize(root):
    path = root / EVENT / 'normal.json'
    if path.exists():
        return read_json(path)
    normal = {'start': START.isoformat(), 'endExclusive': END.isoformat(),
              'depictions': {}, 'featured': {}, 'packageIcons': {}, 'assetSHA256': {}}
    for file in DEPICTIONS:
        data = read_json(root / file)
        normal['depictions'][file] = {key: data.get(key) for key in ('headerImage', 'tintColor')}
    for banner in read_json(root / 'sileo-featured.json')['banners']:
        normal['featured'][banner['package']] = banner['url']
    for record in records((root / 'Packages').read_text(encoding='utf-8')):
        if field(record, 'Package') in SLUGS:
            normal['packageIcons'][identity(record)] = field(record, 'Icon')
    normal['packageFieldsIcon'] = field((root / 'Packages-fields.txt').read_text(encoding='utf-8'), 'Icon')
    for file in NORMAL_ASSETS:
        normal['assetSHA256'][file] = hashlib.sha256((root / file).read_bytes()).hexdigest()
    save_json(path, normal)
    return normal

def rebuild_index(root, raw, now):
    (root / 'Packages').write_bytes(raw)
    (root / 'Packages.gz').write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    (root / 'Packages.bz2').write_bytes(bz2.compress(raw, compresslevel=9))
    (root / 'Packages.xz').write_bytes(lzma.compress(raw, preset=9))
    header = (root / 'Release').read_text(encoding='utf-8').split('MD5Sum:', 1)[0]
    header = re.sub(r'^Date:.*$', 'Date: ' + format_datetime(now.astimezone(timezone.utc), usegmt=True), header, flags=re.M)
    for title, algorithm in [('MD5Sum', 'md5'), ('SHA1', 'sha1'), ('SHA256', 'sha256'), ('SHA512', 'sha512')]:
        header += title + ':\n'
        for file in ('Packages', 'Packages.gz', 'Packages.bz2', 'Packages.xz'):
            content = (root / file).read_bytes()
            header += f' {hashlib.new(algorithm, content).hexdigest()} {len(content):16d} {file}\n'
    (root / 'Release').write_bytes(header.encode())

def reconcile(root, now):
    if now.tzinfo is None:
        raise ValueError('Use an ISO timestamp with an explicit UTC offset')
    normal = initialize(root)
    active = START <= now < END
    changed = []
    for file, slug in DEPICTIONS.items():
        data = read_json(root / file)
        updated = False
        for key, event_value in [('headerImage', BASE + slug + '-banner.jpg'), ('tintColor', '#F9A8CE')]:
            current = data.get(key)
            if active:
                # Preserve a newer normal asset before replacing it for the event.
                if current != event_value and current != normal['depictions'][file][key]:
                    normal['depictions'][file][key] = current
                value = event_value
            else:
                value = normal['depictions'][file][key] if current == event_value else current
            if current != value:
                if value is None: data.pop(key, None)
                else: data[key] = value
                updated = True
        if updated:
            save_json(root / file, data); changed.append(file)
    file = 'sileo-featured.json'
    data = read_json(root / file); updated = False
    for banner in data['banners']:
        package = banner['package']
        if package not in SLUGS: continue
        event_url = BASE + SLUGS[package] + '-featured.jpg'
        if active:
            if banner['url'] != event_url: normal['featured'][package] = banner['url']
            value = event_url
        else:
            value = normal['featured'][package] if banner['url'] == event_url else banner['url']
        if banner['url'] != value: banner['url'] = value; updated = True
    if updated: save_json(root / file, data); changed.append(file)
    before = (root / 'Packages').read_text(encoding='utf-8')
    result = []
    icon_count = 0
    for record in records(before):
        package = field(record, 'Package')
        if package in SLUGS:
            key = identity(record); current = field(record, 'Icon')
            event_url = BASE + SLUGS[package] + '-icon-192.png'
            if active:
                if current != event_url: normal['packageIcons'][key] = current
                value = event_url
            else:
                if current == event_url and key not in normal['packageIcons']:
                    raise ValueError('Missing normal icon for ' + key)
                value = normal['packageIcons'][key] if current == event_url else current
            if current != value:
                record = replace_field(record, 'Icon', value); icon_count += 1
        result.append(record)
    raw = '\n\n'.join(result) + '\n\n'
    if icon_count:
        rebuild_index(root, raw.encode(), now)
        changed.extend(['Packages', 'Packages.gz', 'Packages.bz2', 'Packages.xz', 'Release'])
    file = 'Packages-fields.txt'
    before = (root / file).read_text(encoding='utf-8'); current = field(before, 'Icon')
    event_url = BASE + 'evocenter-icon-192.png'
    if active:
        if current != event_url: normal['packageFieldsIcon'] = current
        value = event_url
    else:
        value = normal['packageFieldsIcon'] if current == event_url else current
    if current != value:
        (root / file).write_bytes((replace_field(before.rstrip('\n'), 'Icon', value) + '\n').encode())
        changed.append(file)
    path = root / EVENT / 'normal.json'
    if read_json(path) != normal:
        save_json(path, normal); changed.append(EVENT + '/normal.json')
    return {'active': active, 'start': START.isoformat(), 'endExclusive': END.isoformat(),
            'checkedAt': now.isoformat(), 'changed': changed, 'packageIconsChanged': icon_count}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--at', help='ISO timestamp; default: current UTC time')
    parser.add_argument('--initialize', action='store_true')
    parser.add_argument('--status-file', type=Path)
    args = parser.parse_args()
    if args.initialize:
        normal = initialize(args.root)
        print(f"Preserved {len(normal['packageIcons'])} package icons and {len(normal['assetSHA256'])} original image hashes.")
    else:
        now = datetime.fromisoformat(args.at.replace('Z', '+00:00')) if args.at else datetime.now(timezone.utc)
        status = reconcile(args.root, now)
        if args.status_file: save_json(args.status_file, status)
        print(json.dumps(status, ensure_ascii=False))
