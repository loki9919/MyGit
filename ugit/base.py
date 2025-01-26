from . import data
import os

def write_tree (directory='.'):
    entries = []
    with os.scandir (directory) as it:
        for entry in it:
            full = f'{directory}/{entry.name}'
            if is_ignored(full):
                continue
            if entry.is_file (follow_symlinks=False):
                with open(full, 'rb') as f:
                    file_content = f.read()
                oid = data.hash_object(file_content, type_='blob')
                entries.append(f'blob{oid}{entry.name}\n')
            elif entry.is_dir (follow_symlinks=False):
                oid = write_tree(full)
                entries.append(f'tree{oid}{entry.name}\n')

    tree_string = ''.join(entries).encode()
    oid = data.hash_object(tree_string, type_='tree')
    return oid

def is_ignored(path):
    return '.ugit' in path.split('/')