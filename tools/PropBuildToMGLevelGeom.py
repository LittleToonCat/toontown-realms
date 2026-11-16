"""
Quickly made Prop Build to Minigame Level Geometry converter
This isn't done yet, actual production version will contain a UI
"""

import argparse, json
from typing import Dict, Union, TextIO, Any

parser = argparse.ArgumentParser(
    description = 'This script can be used to convert Prop Generator files to Level Geometry Data')
parser.add_argument('inputfile', help = 'The Input prop-gen file')
parser.add_argument('--output', help = 'Export Name')
args = parser.parse_args()

infile: TextIO
with open(args.inputfile, 'r') as infile:
    pgen: Dict[Any, Any] = json.loads(infile.read())

    minigameGeom: Dict[str, Union[int, Dict[str, str], list]] = {
        "prophunt_map_version": 1,
        'map_info': {
            "identifier": "drewcification:testmap",
            "name": "Test Map!!",
            "author": "drewcification"
        },
        'prop_spawn_locations': [],
        'allowed_props': [],
        'level_geometry': []
    }

    prop: Dict
    for prop in pgen:
        if prop != 'propgen_version':
            prop = pgen[prop]
            if 'color_scale' in prop['Data']:
                color = prop['Data']['color_scale']
            else:
                color = (1.0, 1.0, 1.0, 1.0)
            minigameGeom['level_geometry'].append({
                "type": "prop",
                "path": prop['PropType'],
                "pos": prop['Position'],
                "hpr": prop['Rotation'],
                "scale": prop['Scale'],
                "color": color
            })

    outfile: TextIO
    with open(args.output, 'w') as outfile:
        outfile.write(json.dumps({'level_geometry': minigameGeom}, indent = 2))
    print(f'Outputted to {outfile}')
