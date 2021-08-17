#!/usr/bin/env python

import os
import sys
import json
import shutil
import pathlib
from time import time


def load(path: pathlib.Path) -> dict:
    if path.exists():
        with open(path) as file:
            return json.load(file)
    return {}
def dump(content, path: pathlib.Path) -> dict:
    with open(path, 'w') as file:
        return json.dump(content, file, indent=4)
def escape(s):
    return str(s).replace('\\', '\\\\').replace('"', '\\"')
def remove(path: pathlib.Path):
    if path.exists():
        if path.is_dir():
            if sys.platform == 'win32':
                os.system(f'rd "{escape(path)}" /s/q')
            else:
                shutil.rmtree(path)
        elif sys.platform == 'win32':
            os.system(f'del "{escape(path)}" /s/q')
        else:
            os.remove(path)
def copy(source: pathlib.Path, dest: pathlib.Path):
    remove(dest)
    if source.is_dir():
        if sys.platform == 'win32':
            os.system(f'xcopy "{escape(source)}\\\\." "{escape(dest)}" /h/s/i/k/f/q')
        else:
            shutil.copytree(source, dest)
    elif sys.platform == 'win32':
        os.system(f'copy "{escape(source)}" "{escape(dest)}" /b')
    else:
        shutil.copyfile(source, dest)


PROJECT_NAME = pathlib.Path(__file__).parent.parent.name
PROJECT_ROOT = pathlib.Path(__file__).parent.parent


def Path(*args):
    return pathlib.Path(PROJECT_ROOT, *map(lambda x: x.replace('$PROJECT_DIR$', str(PROJECT_ROOT)) if isinstance(x, str) else x, args))


config = load(Path('config.json'))
device = load(Path('device.json'))
tdnproj = load(Path('.tdnproj'))
tdnbuild = load(Path('.tdnbuild'))


NAMESPACE = tdnproj.get('default-namespace', PROJECT_NAME.replace(' ', '_').lower())


DATAPACK_SOURCE = Path(tdnbuild['output']['directories']['data-pack'])
RESOURCEPACK_SOURCE = Path(tdnbuild['output']['directories']['resource-pack'])


t = time()
# Remove all functions tagged #minecraft:remove
to_be_removed = load(DATAPACK_SOURCE.joinpath('data', 'minecraft', 'tags', 'functions', 'remove.json')).get('values', [])
for func in to_be_removed:
    namespace, body = func.split(':')
    path = DATAPACK_SOURCE.joinpath('data', namespace, 'functions', body + '.mcfunction')
    os.remove(path)
    while len(os.listdir(path.parent)) == 0:
        os.rmdir(path.parent)
        path = path.parent

if DATAPACK_SOURCE.joinpath('data', 'minecraft', 'tags', 'functions', 'remove.json').exists():
    path = DATAPACK_SOURCE.joinpath('data', 'minecraft', 'tags', 'functions', 'remove.json')
    os.remove(path)
    while len(os.listdir(path.parent)) == 0 and path.parent.resolve() != DATAPACK_SOURCE.resolve():
        os.rmdir(path.parent)
        path = path.parent
print(f'Removed functions tagged #minecraft:remove in {time() - t:.2f} seconds')
t = time()


if config.get('prefer-schedule', True):
    # Remove #minecraft:tick in favor of scheduling
    tick = Path(DATAPACK_SOURCE, 'data', 'minecraft', 'tags', 'functions', 'tick.json')
    if tick.exists():
        # Get an available name for the schedule function and tag
        i = 0
        tick_tag = Path(DATAPACK_SOURCE, 'data', NAMESPACE, 'tags', 'functions', '__tick__.json')
        while tick_tag.exists():
            tick_tag = Path(DATAPACK_SOURCE, 'data', NAMESPACE, 'tags', 'functions', f'__tick__{i}.json')
            i += 1
        tick_tag.parent.mkdir(parents=True, exist_ok=True)

        i = 0
        tick_function = Path(DATAPACK_SOURCE, 'data', NAMESPACE, 'functions', '__tick__.mcfunction')
        while tick_function.exists():
            tick_function = Path(DATAPACK_SOURCE, 'data', NAMESPACE, 'functions', f'__tick__{i}.mcfunction')
            i += 1
        tick_function.parent.mkdir(parents=True, exist_ok=True)

        # Move #minecraft:tick to the tick tag
        shutil.move(tick, tick_tag)

        # Write the tick function, which schedule itself after 1 tick
        with open(tick_function, 'w') as file:
            file.write(f'function #{NAMESPACE}:{tick_tag.stem}\nschedule function {NAMESPACE}:{tick_function.stem} 1t')

        # Add the tick function to the load tag
        load_tag = Path(DATAPACK_SOURCE, 'data', 'minecraft', 'tags', 'functions', 'load.json')
        if load_tag.exists():
            load_json = load(load_tag)
            if 'values' not in load_json:
                load_json['values'] = []
        else:
            load_json = {'values': []}
        load_json['values'].append(f'{NAMESPACE}:{tick_function.stem}')
        dump(load_json, load_tag)
    print(f'Removed #minecraft:tick in favor of scheduling in {time() - t:.2f} seconds')
    t = time()


# Copy to world
WORLD = config.get('link-to-world')
if WORLD:
    if 'minecraft-directory' in device:
        MINECRAFT_DIRECTORY = Path(device['minecraft-directory'])
    elif sys.platform == 'win32':
        MINECRAFT_DIRECTORY = Path(os.getenv('APPDATA'), '.minecraft')
    elif sys.platform == 'linux':
        MINECRAFT_DIRECTORY = pathlib.Path.home().joinpath('.minecraft')
    elif sys.platform == 'darwin':
        MINECRAFT_DIRECTORY = pathlib.Path.home().joinpath('Library', 'Application Support', 'minecraft')
    else:
        MINECRAFT_DIRECTORY = Path(os.path.expanduser(os.path.expandvars(
            input('Unknown operating system. Please input minecraft install directory manually: ')
        )))
    device['minecraft-directory'] = str(MINECRAFT_DIRECTORY.resolve())
    DATAPACK = MINECRAFT_DIRECTORY.joinpath('saves', WORLD, 'datapacks', DATAPACK_SOURCE.name)
    RESOURCEPACK = MINECRAFT_DIRECTORY.joinpath('saves', WORLD, 'resources')

    copy(DATAPACK_SOURCE, DATAPACK)
    copy(RESOURCEPACK_SOURCE, RESOURCEPACK)
    print(f'Copied to world in {time() - t:.2f} seconds')
    t = time()

    if len(os.listdir(DATAPACK_SOURCE.parent)) == 0:
        os.rmdir(DATAPACK_SOURCE.parent)
    
    
dump(config, Path('config.json'))
dump(device, Path('device.json'))
