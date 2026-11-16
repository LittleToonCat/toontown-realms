import glob
import json
import os.path
import logging
from pathlib import PurePosixPath
from typing import Dict, List

from panda3d.core import Multifile, Filename

Packs: Dict[str, List[str]] = {}


def sortTextures():
    mf: int = 1
    size: int = 0
    allassets = []
    for p in [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]:
        assets = glob.glob(f'phase_{p}/maps/**/?*.png', recursive = True)
        assets.sort()
        allassets.extend(assets)

    for asset in allassets:
        fs = os.path.getsize(asset)

        if size + fs >= .5E+8:
            mf += 1
            size = fs
        else:
            size += fs

        if f"ttrm_tex_{mf:02d}.mf" not in Packs:
            Packs[f"ttrm_tex_{mf:02d}.mf"] = []
        Packs[f"ttrm_tex_{mf:02d}.mf"].append(asset)


def sortModels():
    mf: int = 1
    msize: int = 0
    allmdl = []
    for p in [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]:
        assets = glob.glob(f'phase_{p}/models/**/?*.bam', recursive = True)
        assets.sort()
        allmdl.extend(assets)

    for tex in allmdl:
        fs = os.path.getsize(tex)

        if msize + fs >= .5E+8:
            mf += 1
            msize = fs
        else:
            msize += fs

        if f"ttrm_mdl_{mf:02d}.mf" not in Packs:
            Packs[f"ttrm_mdl_{mf:02d}.mf"] = []
        Packs[f"ttrm_mdl_{mf:02d}.mf"].append(tex)


def sortAud():
    mf: int = 1
    size: int = 0
    allassets = []
    for p in [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]:
        assets = glob.glob(f'phase_{p}/audio/**/?*.ogg', recursive = True)
        assets.sort()
        allassets.extend(assets)

    for asset in allassets:
        fs = os.path.getsize(asset)

        if size + fs >= .5E+8:
            mf += 1
            size = fs
        else:
            size += fs

        if f"ttrm_aud_{mf:02d}.mf" not in Packs:
            Packs[f"ttrm_aud_{mf:02d}.mf"] = []
        Packs[f"ttrm_aud_{mf:02d}.mf"].append(asset)


def sortData():
    mf: int = 1
    size: int = 0
    allassets = []
    for p in [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]:
        assets = glob.glob(f'phase_{p}/data/**/?*.*', recursive = True)
        assets = glob.glob(f'phase_{p}/models/**/?*.rgb', recursive = True)
        assets = glob.glob(f'phase_{p}/models/**/?*.cur', recursive = True)
        assets = glob.glob(f'phase_{p}/models/**/?*.ico', recursive = True)
        assets.extend(glob.glob(f'phase_{p}/dna/**/?*.*', recursive = True))
        assets.extend(glob.glob(f'phase_{p}/etc/**/?*.*', recursive = True))
        assets.extend(glob.glob(f'phase_{p}/filters/**/?*.*', recursive = True))
        assets.extend(glob.glob(f'phase_{p}/fonts/**/?*.*', recursive = True))
        assets.sort()
        allassets.extend(assets)

    for asset in allassets:
        fs = os.path.getsize(asset)

        if size + fs >= .5E+8:
            mf += 1
            size = fs
        else:
            size += fs

        if f"ttrm_dat_{mf:02d}.mf" not in Packs:
            Packs[f"ttrm_dat_{mf:02d}.mf"] = []
        Packs[f"ttrm_dat_{mf:02d}.mf"].append(asset)


def sortSha():
    mf: int = 1
    size: int = 0
    allassets = []
    for p in [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]:
        assets = glob.glob(f'phase_{p}/shaders/**/?*.*', recursive = True)
        assets.sort()
        allassets.extend(assets)

    for asset in allassets:
        fs = os.path.getsize(asset)

        if size + fs >= .5E+8:
            mf += 1
            size = fs
        else:
            size += fs

        if f"ttrm_sha_{mf:02d}.mf" not in Packs:
            Packs[f"ttrm_sha_{mf:02d}.mf"] = []
        Packs[f"ttrm_sha_{mf:02d}.mf"].append(asset)

logging.basicConfig(level = logging.DEBUG, format = "[%(levelname)s] %(asctime)s: %(message)s")
sortTextures()
sortModels()
sortAud()
sortData()
sortSha()

datalist: List[str]
for pack, datalist in Packs.items():
    logging.debug(f'Writing {pack} ({len(datalist)} files)')
    m = Multifile()
    m.openWrite(pack)

    for i in datalist:
        i = i.replace("\\", "/")
        i = str(PurePosixPath(i))
        fn = Filename(i)
        fn.setBinary()
        m.addSubfile(i, fn, 0)

    m.flush()
    m.close()
