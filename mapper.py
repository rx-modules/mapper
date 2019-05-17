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

"""
TODO: use logger?
TODO: global variables, but it's probably ok
"""


def gen_pastel_color():
    """ generates pastel colors through a formula (adding 255 then halving """
    triplet = (
        round((random.randrange(0, 255) + 255) / 2),
        round((random.randrange(0, 255) + 255) / 2),
        round((random.randrange(0, 255) + 255) / 2)
    )
    # transform triple to '#ffffff' form
    return str(b'#'+b16encode(bytes(triplet)))[1:].replace("'", '').lower().strip()  # noqa


def trace(source, lead=None):
    """ debug generator that can wrap any generator to print items """
    if lead is None:
        lead = source.__name__
    for item in source:
        print(lead + ': ' + str(item))
        yield item


def convert(fname, num=4):
    """ converts file path to mc namespaced path """
    parts = Path(fname).parts  # 0:1 - datapack/data, 3 - functions
    return parts[2] + ':' + '/'.join(re.sub(r'(\.mcfunction)|(\.json)', '', part) for part in parts[num:])  # noqa


def gen_open(paths):
    """ opens path and returns 'em """
    global fcount
    for path in paths:
        fcount += 1
        yield path.open()


def gen_lines(files):
    """ reads file into lines and yields a tuple: (mc path, line) """
    for file in files:
        lines = file.readlines()
        name = file.name
        file.close()
        for line in lines:
            yield convert(name), line


def gen_grep(pat, tups):
    """ filter input through pattern searching """
    # TODO: move .replace's elsewhere
    for name, line in tups:
        if pat.search(line):
            yield name, line.replace(' run', '').replace('execute ', '').strip()  # noqa


def gen_do(pat, tup):
    """
    takes in the func pattern and yields each mc name with it's call and label
    """
    for name, line in tup:
        match = pat.search(line)
        if match.group(1).strip() == 'schedule function':
            time = match.group(4).strip()
        else:
            time = ''

        func = match.group(3)
        label = line[:match.start()].strip() + ' ' + time
        yield name, func, label


def gen_tag(paths):
    """ takes in paths for func tags and yields the name and what it calls """
    for path in paths:
        namespaced = '#' + convert(path, 5)  # path.__repl__() -> str
        jfile = json.load(path.open())
        for val in jfile['values']:
            yield namespaced, val, ''


def gen_adv(paths):
    """ takes in paths for advs and yields the name and the reward """
    for path in paths:
        jfile = json.load(path.open())
        if 'rewards' in jfile:  # rewards has the function output
            yield str(path), jfile['rewards']['function'], ''


def get_paths(dir_name, glob):
    """ returns a generator of the recursive paths on input glob """
    return Path(f'./{dir_name}/data').rglob(glob)


def get_functions(dir_name):
    """ packaged generators that handle functions """
    pat = re.compile(r'^((?!^#.+).)*$')
    patf = re.compile(r'((schedule )?function(?![^{]*})) (#?[a-z0-9.-_+:]+)( \d+.)?')  # noqa
    funcnames = get_paths(dir_name, '*/functions/**/*.mcfunction')
    funcfiles = gen_open(funcnames)
    functuple = gen_lines(funcfiles)
    funclines = gen_grep(patf, functuple)
    funcfuncs = gen_grep(pat, funclines)
    return gen_do(patf, funcfuncs)


def get_tags(dir_name):
    """ packaged generators that handle function tags """
    jsonnames = get_paths(dir_name, '*/tags/functions/*.json')
    return gen_tag(jsonnames)


def get_adv(dir_name):
    """ packaged generators that handle advancements """
    advjnames = get_paths(dir_name, '*/advancements/**/*.json')
    return gen_adv(advjnames)


def stream_nodes(datapack):
    """ combines all three packages in one generator stream """
    functions = get_functions(datapack)
    functags = get_tags(datapack)
    advnames = get_adv(datapack)
    return chain(functions, functags, advnames)


def build_graph(G, gen, lab, datapack):
    """ builds graphviz graph through a generator """
    fecount = 0

    for func in gen:
        fecount += 1
        name, call, label = func
        color = gen_pastel_color()
        if name.startswith('#') or '.json' in name:  # if tag or adv
            G.add_node(name.strip(), color=color, fontcolor=color)
        else:
            G.add_node(name.strip())

        if call != '':
            if lab:
                G.add_edge(name, call.strip(),
                           color=color, fontcolor=color, label=label)
            else:
                G.add_edge(name, call.strip(),
                           color=color)

    print(f'  {datapack} built with: {fcount} functions and {fecount} connections ({G.order()} nodes)!')  # noqa


def output_graph(dir_name, G, outfile):
    """ displays the graph to jpeg (and .dot) """
    if outfile is None:
        outfile = dir_name  # dir_name can be our outfile
    print(f'Constructing the {outfile} graph. Warning: This might take a while')  # noqa
    print('  Laying graph out')
    G.layout()  # lays out the graph. not neccissary, but helps with final product # noqa
    print(f'  Writing to {outfile}.dot')
    G.write(f'{outfile}.dot')  # this file can be displayed again through any graphviz program # noqa
    print(f'  Drawing to {outfile}.jpeg')
    G.draw(f'{outfile}.jpeg', format='jpeg', prog='sfdp')


def main(datapacks, mode='one', label=False, outfile=None):
    global fcount
    start = time.time()

    # labeling doesn't work properly on smart overlap (=False)
    # on scale, the output picture get's pretty big, but looks neater
    if label:
        overlap = 'scale'
    else:
        overlap = False

    # mode: one, loop each datapack on building then output
    # mode: multiple, loop each datapack and output each one
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
            build_graph(G, nodes, label, datapack)
            fcount = 0

        output_graph(datapacks[0], G, outfile)
    elif mode == 'multiple':
        for datapack in datapacks:
            # strict=False and directed=True allows self-loops
            G = pgv.AGraph(splines=True,
                           overlap=overlap,
                           strict=False,
                           directed=True,
                           bgcolor='#262626')
            G.node_attr.update(color='white', fontcolor='#bfbfbf')

            print('Reading in the datapack and building the graph')
            nodes = stream_nodes(datapack)
            build_graph(G, nodes, label, None)  # None, otherwise each file named same # noqa
            output_graph(datapack, G)
            fcount = 0
    else:
        print('Invalid Mode')
        print('Please notify the repo maintainers if you see this')
        input('Press enter to quit')
        sys.exit()

    print(f'Done in {round(abs(start - time.time()), 3)}s!')


if __name__ == '__main__':
    parser = ArgumentParser(description='minecraft datapack mapper using graphviz')  # noqa
    parser.add_argument('datapack', metavar='d', type=str, nargs='+',
                        help='a valid datapack to map')
    parser.add_argument('-m', '--mode', type=str, default='one',
                        help='output all datapacks to [multiple] or [one] graph')  # noqa
    parser.add_argument('-l', '--label', default=False, action='store_true', # noqa
                        help='enable edge labeling (warning, takes longer and bigger output size)')  # noqa
    parser.add_argument('-o', '--outfile', type=str, # noqa
                        help='define what file you would like to save the output to. default: datapack.jpeg/out')  # noqa
    args = parser.parse_args()

    for arg in args.datapack:
        if not Path(arg).exists():
            input('Directory does not exist. Press enter to quit')
            sys.exit()

    main(args.datapack, args.mode, args.label, args.outfile)
