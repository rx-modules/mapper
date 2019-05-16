from base64 import b16encode
from pathlib import Path
from itertools import chain
import pygraphviz as pgv
import random
import json
import time
import re

fcount = 0


def gen_pastel_color():
    triplet = (
        round((random.randrange(0, 255) + 255) / 2),
        round((random.randrange(0, 255) + 255) / 2),
        round((random.randrange(0, 255) + 255) / 2)
    )
    return str(b'#'+b16encode(bytes(triplet)))[1:].replace("'", '').lower().strip()  # noqa


def trace(source, lead='line'):
    for item in source:
        print(lead + ': ' + str(item))
        yield item


def gen_open(paths):
    global fcount
    for path in paths:
        fcount += 1
        yield path.open()

def convert(fname, num=4):
    parts = Path(fname).parts  # 0:1 - datapack/data, 3 - functions
    return parts[2] + ':' + '/'.join(re.sub(r'(\.mcfunction)|(\.json)', '', part) for part in parts[num:])



def gen_lines(files):
    for file in files:
        lines = file.readlines()
        for line in lines:
            yield convert(file.name), line


def gen_grep(pat, tups):
    for name, line in tups:
        if pat.search(line):
            yield name, line.replace(' run', '').replace('execute ', '').strip()  # noqa


def find_namespace(s):
    pass



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


def gen_json(paths):
    for path in paths:
        namespaced = '#' + convert(path, 5)  # path.__repl__() -> str
        jfile = json.load(path.open())
        yield ((namespaced, (val, '')) for val in jfile['values'])


def main():
    fecount = 0
    pat = re.compile(r'^((?!^#.+).)*$')
    patf = re.compile(r'((schedule )?function(?![^{]*})) (#?[a-z0-9.-_+:]+)( \d+.)?')  # noqa

    dir_name = str(input('Datapack name: '))
    start_time = time.time()

    funcfames = Path(f'./{dir_name}/data').rglob('*.mcfunction')
    funcfiles = gen_open(funcfames)
    functuple = gen_lines(funcfiles)
    funclines = gen_grep(patf, functuple)
    funcfuncs = gen_grep(pat, funclines)
    functions = gen_do(patf, funcfuncs)

    jsonfames = Path(f'./{dir_name}/data').rglob('*/tags/functions/*.json')
    functagss = gen_json(jsonfames)
    finaltags = chain.from_iterable(functagss)

    gen_funcs = chain(functions, finaltags)  # Final stop

    G = pgv.AGraph(splines=True,
                   overlap=False,
#                  overlap='scale',  # noqa
                   strict=False,
                   directed=True,
                   bgcolor='#262626')

    G.node_attr.update(color='white', fontcolor='#bfbfbf')

    print('Building graph')
    # test = set()
    for func in gen_funcs:
        fecount += 1
        name, call = func
        G.add_node(name.strip())
        # test.add(name.strip() + '\n')
        called = call[0]
        if called != '':
            G.add_edge(name, called.strip(), color=gen_pastel_color())

    '''
    with open('text.txt', 'w') as file:
        out = ''
        for item in test:
            out += item
        file.write(out)
    '''

    print(f'Built with: {fcount} functions and {fecount} connections ({G.order()} nodes)')  # noqa
    print('Laying graph out')
    G.layout()
    print('Writing to .dot file')
    G.write(f'dots/{dir_name}.dot')
    print('Drawing to jpeg')
    G.draw(f'pics/{dir_name}.jpeg', format='jpeg', prog='sfdp')
    print(f'Done in {round(abs(start_time - time.time()), 3)}s!')


if __name__ == '__main__':
    main()
