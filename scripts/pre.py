#!/usr/bin/env python

import os
import json
import glob
import shutil
import pathlib


PROJECT_ROOT = pathlib.Path(__file__).parent.parent


def Path(*args):
    return pathlib.Path(PROJECT_ROOT, *args)


if Path('.tdnignore').exists() and Path('datapack', 'data').exists():
    with open(Path('.tdnignore')) as file:
        ignores = file.read().split()
        ignores = [line for line in ignores if not line.startswith('#')]
        ignores = [line[1:] if line.startswith('/') else line for line in ignores]

    i = 0
    temp = Path('__temp__')
    if temp.exists():
        with open(temp.joinpath('data.json')) as file:
            data = json.load(file)
        while temp.joinpath(str(i)).exists():
            i += 1
    else:
        temp.mkdir()
        data = {}

    os.chdir(Path('datapack', 'data'))
    for root, dirs, files in os.walk('.', topdown=True):
        for path in (*dirs, *files):
            path = pathlib.Path(root, path)
            for line in ignores:
                if path.match(line):
                    data[str(path.resolve())] = str(i)
                    shutil.move(path, temp.joinpath(str(i)))
                    i += 1
    
    with open(temp.joinpath('data.json'), 'w') as file:
        json.dump(data, file, indent=4)
