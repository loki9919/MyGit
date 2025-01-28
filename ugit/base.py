from . import data
import os
import itertools
import operator
from collections import namedtuple

def write_tree(directory='.'):
    entries = []
    with os.scandir(directory) as it:
        for entry in it:
            full = f'{directory}/{entry.name}'
            if is_ignored(full):
                continue

            oid = None
            type_ = None

            if entry.is_file(follow_symlinks=False):
                type_ = 'blob'
                with open(full, 'rb') as f:
                    oid = data.hash_object(f.read())
            elif entry.is_dir(follow_symlinks=False):
                type_ = 'tree'
                oid = write_tree(full)
            if type_ is not None:
                entries.append((entry.name, oid, type_))

    tree = ''.join(f'{type_}{oid}{name}\n'
                    for name, oid, type_ in sorted(entries))
    return data.hash_object(tree.encode(), 'tree')


def _iter_tree_entries(oid):
    if not oid:
        return
    tree = data.get_object(oid, expected='tree')
    for entry in tree.decode().splitlines():
        parts = entry.split(' ', 2)
        if len(parts) == 3:
          entry_type, entry_oid, entry_name = parts
          yield entry_type, entry_oid, entry_name
        
def get_tree(oid, base_path=''):
    result = {}
    for type_, oid, name in _iter_tree_entries(oid):
        assert '/' not in name
        assert name not in ('..', '.')
        path = base_path + name
        if type_ == 'blob':
            result[path] = oid
        elif type_ == 'tree':
            result.update(get_tree(oid, f'{path}/'))
        else:
            assert False, f'unknown tree entry {type_}'
    return result

def _empty_current_directory():
    for root, dirnames, filenames in os.walk('.', topdown=False):
        for filename in filenames:
            path = os.path.relpath(f'{root}/{filename}')
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
        for dirname in dirnames:
            path = os.path.relpath(f'{root}/{dirname}')
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except(FileNotFoundError, OSError):
                pass

def read_tree(tree_oid):
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid))
            
def commit(message):
    commit = f'tree{write_tree()}\n'
    HEAD = data.get_Head()
    if HEAD:
        commit += f'parent{HEAD}\n'
    commit += '\n'
    commit += f'{message}\n'
    
    oid = data.hash_object(commit.encode(), 'commit')
    data.set_HEAD(oid)
    return oid

commit = namedtuple('commit', ['tree', 'parent', 'message'])

def get_commit(oid):
    parent= None
    
    commit = data.get_object(oid, 'commit').decode()
    lines = iter(commit.splitlines())
    for line in itertools.takewhile(operator.truth, line):
        key, value = line.split(' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parent = value
        else:
            assert False, f'unkown filed {key}'
    message = '\n'.join(lines)
    return commit(tree=tree, parent=parent, message=message)

def is_ignored(path):
    return '.ugit' in path.split('/')