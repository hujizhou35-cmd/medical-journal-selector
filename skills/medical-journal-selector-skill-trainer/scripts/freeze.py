#!/usr/bin/env python3
"""Create a new immutable-by-hash experiment snapshot; never replace an old one."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from corpus import stamp

def freeze(source,destination):
    source=Path(source).resolve()
    destination=Path(destination).resolve()
    if not (source/"SKILL.md").is_file():
        raise ValueError("Source must be a complete Skill folder")
    if destination==source or source in destination.parents:
        raise ValueError("Snapshot must be outside its source folder")
    if destination.exists():
        raise ValueError("Snapshot already exists; do not overwrite a frozen version")
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,destination,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    files={p.relative_to(destination).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destination.rglob("*")) if p.is_file()}
    manifest={"frozen_at":stamp(),"files":files,"source":str(source)}
    (destination/"snapshot-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest

def verify(destination):
    destination=Path(destination)
    manifest=json.loads((destination/"snapshot-manifest.json").read_text(encoding="utf-8"))
    actual={p.relative_to(destination).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.rglob("*") if p.is_file() and p.name!="snapshot-manifest.json" and "__pycache__" not in p.parts and p.suffix!=".pyc"}
    if actual!=manifest["files"]:
        raise ValueError("Frozen snapshot was changed")
    return True

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination",type=Path)
    parser.add_argument("--source",type=Path)
    parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    if args.verify:
        verify(args.destination)
        print("Snapshot unchanged")
    elif args.source:
        freeze(args.source,args.destination)
        print("Snapshot frozen")
    else:
        parser.error("Supply --source or --verify")

if __name__=="__main__":
    main()
