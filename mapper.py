from argparse import ArgumentParser
from base64 import b16encode
from itertools import chain
from pathlib import Path

import pygraphviz as pgv
import random
import json
import time
import sys
import re

fcount = 0


def gen_pastel_color():
    triplet = (
        round((random.randrange(0, 255) + 255) / 2),
        round((random.randrange(0, 255) + 255) / 2),
        round((random.randrange(0, 255) + 255) / 2)
    )
    return str(b'#'+b16encode(bytes(triplet)))[1:].replace("'", '').lower().strip()  # noqa


def trace(source, lead=None):
    if lead is None:
        lead = source.__name__
    for item in source:
        print(lead + ': ' + str(item))
        yield item


def convert(fname, num=4):
    parts = Path(fname).parts  # 0:1 - datapack/data, 3 - functions
    return parts[2] + ':' + '/'.join(re.sub(r'(\.mcfunction)|(\.json)', '', part) for part in parts[num:])  # noqa


def gen_open(paths):
    global fcount
    for path in paths:
        fcount += 1
        yield path.open()


def gen_lines(files):
    for file in files:
        lines = file.readlines()
        for line in lines:
            yield convert(file.name), line


def gen_grep(pat, tups):
    for name, line in tups:
        if pat.search(line):
            yield name, line.replace(' run', '').replace('execute ', '').strip()  # noqa


def gen_do(pat, tup):
    for name, line in tup:
        match = pat.search(line)
        if match.group(1).strip() == 'schedule function':
            time = match.group(4).strip()
        else:
            time = ''

        func = match.group(3)
        label = line[:match.start()].strip() + ' ' + time
        yield name, (func, label)


def gen_tag(paths):
    for path in paths:
        namespaced = '#' + convert(path, 5)  # path.__repl__() -> str
        jfile = json.load(path.open())
        for val in jfile['values']:
            yield (namespaced, (val, ''))


def gen_adv(paths):
    for path in paths:
        jfile = json.load(path.open())
        if 'rewards' in jfile:  # rewards has the function output
            yield (str(path), (jfile['rewards']['function'], ''))


def get_paths(dir_name, glob):
    return Path(f'./{dir_name}/data').rglob(glob)


def get_functions(dir_name):
    pat = re.compile(r'^((?!^#.+).)*$')
    patf = re.compile(r'((schedule )?function(?![^{]*})) (#?[a-z0-9.-_+:]+)( \d+.)?')  # noqa
    funcnames = get_paths(dir_name, '*/functions/**/*.mcfunction')
    funcfiles = gen_open(funcnames)
    functuple = gen_lines(funcfiles)
    funclines = gen_grep(patf, functuple)
    funcfuncs = gen_grep(pat, funclines)
    return gen_do(patf, funcfuncs)


def get_tags(dir_name):
    jsonnames = get_paths(dir_name, '*/tags/functions/*.json')
    return gen_tag(jsonnames)


def get_adv(dir_name):
    advjnames = get_paths(dir_name, '*/advancements/**/*.json')
    return gen_adv(advjnames)


def stream_nodes(datapack):
    functions = get_functions(datapack)
    functags = get_tags(datapack)
    advnames = get_adv(datapack)
    return chain(functions, functags, advnames)


def build_graph(G, gen, label):
    fecount = 0

    for func in gen:
        fecount += 1
        name, call = func
        G.add_node(name.strip())
        called = call[0]
        if called != '':
            color = gen_pastel_color()
            if label:
                G.add_edge(name, called.strip(),
                           color=color, font_color=color, label=call[1]
                )
            else:
                G.add_edge(name, called.strip(),
                           color=color
                )
    print(f'  Built with: {fcount} functions and {fecount} connections ({G.order()} nodes)!')  # noqa


def output_graph(dir_name, G):
    print(f'Constructing the {dir_name} graph. Warning: This might take a while')  # noqa
    print('  Laying graph out')
    G.layout()
    print(f'  Writing to {dir_name}.dot')
    G.write(f'{dir_name}.dot')
    print(f'  Drawing to {dir_name}.jpeg')
    G.draw(f'{dir_name}.jpeg', format='jpeg', prog='sfdp')

def main(datapacks, mode='one', label=False):
    start = time.time()
    
    if label:
        overlap = 'scale'
    else:
        overlap = False

    if mode == 'one':
        G = pgv.AGraph(splines=True,
                       overlap=overlap,
                       strict=False,
                       directed=True,
                       bgcolor='#262626')

        G.node_attr.update(color='white', fontcolor='#bfbfbf')
        print('Reading in the datapacks and building the graph')
        for datapack in datapacks:
            nodes = stream_nodes(datapack)
            build_graph(G, nodes, label)

        output_graph(datapack, G)
    elif mode == 'multiple':
        for datapack in datapacks:
            G = pgv.AGraph(splines=True,
                           overlap=overlap,
                           strict=False,
                           directed=True,
                           bgcolor='#262626')

            G.node_attr.update(color='white', fontcolor='#bfbfbf')
            print('Reading in the datapack and building the graph')
            nodes = stream_nodes(datapack)
            build_graph(G, nodes, label)
            output_graph(datapack, G)
    else:
        print('Invalid Mode')

    
    print(f'Done in {round(abs(start - time.time()), 3)}s!')


if __name__ == '__main__':
    parser = ArgumentParser(description='minecraft datapack mapper using graphviz')  # noqa
    parser.add_argument('datapack', metavar='d', type=str, nargs='+',
                        help='a valid datapack to map')
    parser.add_argument('--mode', type=str, default='one',
                        help='output all datapacks to [multiple] or [one] graph')  # noqa
    parser.add_argument('--label', default=False, action='store_true', # noqa
                        help='enable edge labeling (warning, takes longer and bigger output size)')  # noqa
    args = parser.parse_args()

    for arg in args.datapack:
        if not Path(arg).exists():
            print('Directory does not exist. Stopping..')
            sys.exit()

    main(args.datapack, args.mode, args.label)
