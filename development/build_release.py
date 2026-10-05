#!/usr/bin/env python3
"""Build three install formats for an explicit target, preserving published bytes."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/medical-journal-selector'
TRAINER = ROOT / 'skills/medical-journal-selector-skill-trainer'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def portable(skill=SKILL):
    text = (skill / 'SKILL.md').read_text(encoding='utf-8')
    text += '\n\n# Portable edition: inlined references\n\nAll references below are included in this file. If a relative reference cannot be opened, read its matching section below. Executable helpers are optional and are shipped only in the full bundles; apply their documented rules manually when unavailable.\n'
    for ref in sorted((skill / 'references').glob('*.md')):
        text += '\n---\n\n## Inlined reference: '+ref.name+'\n\n'+ref.read_text(encoding='utf-8')
    return text

def bundle(path, entries, legacy=False):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            # V1 was published with Windows ZIP attributes; use those on all hosts.
            info.create_system = 0 if legacy else 3
            info.external_attr = (0o644 if legacy else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload.replace(b'\r\n', b'\n'))

def inventory():
    return json.loads((ROOT / 'development/releases/distribution.json').read_text(encoding='utf-8'))

def build(target, output=None):
    if target not in ('stable', 'experimental', 'trainer'):
        raise ValueError('Choose stable, experimental or trainer explicitly')
    tag = {'stable':'v1.0.0','experimental':'v2.0.0-experimental.1','trainer':'trainer-v1.0.0'}[target]
    output = Path(output or ROOT / 'dist' / target).resolve()
    if output == ROOT or ROOT in output.parents and (ROOT / 'dist') not in output.parents:
        raise ValueError('Build output inside this repository must be below dist/')
    if output.is_symlink() or any(p.is_symlink() for p in output.parents):
        raise ValueError('Build output cannot use symbolic links')
    output.mkdir(parents=True, exist_ok=True)
    prefix = 'medical-journal-selector'+('-skill-trainer' if target=='trainer' else '')
    version = '2.0.0-experimental.1' if target=='experimental' else '1.0.0'
    names = [prefix+'-v'+version+'.skill',prefix+'-codex-plugin-v'+version+'.zip','SKILL.md']
    if any(p.name not in names or not p.is_file() or p.is_symlink() for p in output.iterdir()):
        raise ValueError('Output must contain only this target\'s three install files')
    if target=='experimental':
        import experimental_release
        with tempfile.TemporaryDirectory() as temp:
            built = experimental_release.build(output=Path(temp)/'artifacts')
            for name in names: shutil.copyfile(built/name,output/name)
    elif target=='stable':
        commit = inventory()['releases'][tag]['source_commit']
        source_prefix = 'skills/medical-journal-selector/'
        paths = git('ls-tree','-r','--name-only',commit,source_prefix).decode().splitlines()
        entries = {p[len(source_prefix):]:git('show',commit+':'+p) for p in paths}
        entries['LICENSE'] = git('show',commit+':LICENSE')
        bundle(output/names[0],entries,legacy=True)
        plugin = {source_prefix+k:v for k,v in entries.items() if k!='LICENSE'}
        plugin.update({'LICENSE':entries['LICENSE'],'.codex-plugin/plugin.json':git('show',commit+':.codex-plugin/plugin.json')})
        bundle(output/names[1],plugin,legacy=True)
        (output/'SKILL.md').write_bytes(git('show',commit+':SKILL.md'))
    else:
        source_prefix = 'skills/medical-journal-selector-skill-trainer/'
        paths = git('ls-files',source_prefix).decode().splitlines()
        if not paths: raise ValueError('No tracked Trainer sources')
        entries = {}
        for p in paths:
            path = ROOT/p
            if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
                raise ValueError('Trainer source cannot be a symbolic link')
            entries[p[len(source_prefix):]] = path.read_bytes()
        entries['LICENSE'] = (ROOT/'LICENSE').read_bytes()
        entries['RELEASE-NOTICE.md'] = b'# Trainer companion preview\n\nThis tool organizes Skill development and evaluation; it does not train model weights. Software checks do not establish overall recommendation improvement.\n'
        bundle(output/names[0],entries)
        plugin = {source_prefix+k:v for k,v in entries.items() if k not in ('LICENSE','RELEASE-NOTICE.md')}
        plugin.update({k:entries[k] for k in ('LICENSE','RELEASE-NOTICE.md')})
        metadata = json.loads((ROOT/'development/trainer-plugin.json').read_text(encoding='utf-8'))
        if metadata['version'] != version: raise ValueError('Trainer version mismatch')
        plugin['.codex-plugin/plugin.json'] = (json.dumps(metadata,ensure_ascii=False,indent=2)+'\n').encode()
        bundle(output/names[1],plugin)
        (output/'SKILL.md').write_text(portable(TRAINER),encoding='utf-8',newline='\n')
    hashes = {name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in names}
    if target in ('stable','experimental'):
        expected = inventory()['releases'][tag]['assets']
        if any(hashes[name]!=expected[name] for name in names):
            raise ValueError('Generated bytes differ from the original published '+tag+' assets')
    return {'tag':tag,'assets':hashes}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',required=True,choices=('stable','experimental','trainer'))
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.target,args.output),indent=2))

if __name__=='__main__': main()
