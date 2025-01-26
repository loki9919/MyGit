import argparse
import os
import sys
from . import data, base

def main():
    args = parse_args()
    args.func(args)
    
    
def parse_args():
    parser = argparse.ArgumentParser()
    
    commands  = parser.add_subparsers(dest='command')
    commands.required = True
    
    init_parser = commands.add_parser('init')
    init_parser.set_defaults(func=init)
    
    # hop: hash object parser
    hop = commands.add_parser('hash-object')
    hop.set_defaults(func=hash_object)
    hop.add_argument('file')
    
    # cat: cat file parser
    cat = commands.add_parser('cat-file')
    cat.set_defaults(func=cat_file)
    cat.add_argument('object')
    
    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)
    
    return parser.parse_args()

def init(args):
    data.init()
    print(f'Initialized empty ugit repostry in {os.getcwd()}/{data.GIT_DIR}')

def hash_object(args):
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read()))

def cat_file(args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))

def write_tree(args):
    print(base.write_tree())