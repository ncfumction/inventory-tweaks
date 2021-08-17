#!/usr/bin/env python

import json
import shutil
import pathlib


PROJECT_ROOT = pathlib.Path(__file__).parent.parent


def Path(*args):
    return pathlib.Path(PROJECT_ROOT, *args)


temp = Path(f'__temp__')
if temp.exists():
    with open(temp.joinpath('data.json')) as file:
        data = json.load(file)

    for k, v in data.items():
        shutil.move(temp.joinpath(v), k)
    shutil.rmtree(temp)