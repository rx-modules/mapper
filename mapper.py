from base64 import b16encode
import pygraphviz as pgv
import random
import time
import os


def gen_pastel_color():
    triplet = (
            round((random.randrange(0, 255) + 255) / 2),
            round((random.randrange(0, 255) + 255) / 2),
            round((random.randrange(0, 255) + 255) / 2)
    )
    return str(b'#'+b16encode(bytes(triplet)))[1:].replace("'", '').lower().strip()


def get_function(fname):
    name = fname[fname.find('data/') + 5:]
    slash = name.find('/')
    name = name[:slash] + ':' + name[slash + 11:]  # / -> : + functions/ -> ''
    calls = []
    with open(fname) as file:
        lines = file.read().split('\n')

        for line in lines:
            line = line.strip()
            if line != '' and line[0] != '#' and 'function' in line:
                index = line.find('function')
                connection = line[:index].replace(' run', '')
                connection = connection.replace('execute ', '').strip()
                call_file = line[index + len('function'):].strip()  # noqa

                calls.append((call_file, connection))

    return name, calls


if __name__ == '__main__':
    dir_name = str(input('Datapack name: '))
    start_time = int(time.time())
    funcs = []
    print('Starting Dir Walk')
    for root, _, files in os.walk(dir_name):
        for file in files:
            fname = root + '/' + file
            if '.mcfunction' in fname:
                funcs.append(get_function(fname))
    print('func -> dict')
    funcs = dict(funcs)
    print('Generating graph attributes')
    G = pgv.AGraph(splines=True,
                   overlap=False,
#                  overlap='scale',
                   strict=False,
                   directed=True,
                   bgcolor='#262626')
    G.node_attr.update(color='white', fontcolor='#bfbfbf')
    # G.edge_attr.update(color='white', fontcolor='#bfbfbf')
    print(f'Building Graph with {len(funcs)} functions')
    for name, calls in funcs.items():
        name = name.replace('.mcfunction', '').strip()
        G.add_node(name)
        for call in calls:
            color = gen_pastel_color()
            G.add_edge(name, call[0], color=color, fontcolor=color)
    # G = G.unflatten('-f -l 1')
    # timeit()
    print('Laying graph out')
    G.layout()
    print('Writing to .dot file')
    G.write(f"{dir_name}.dot")
    print('Drawing to jpeg')
    G.draw(f'pics/{dir_name}.jpeg', format='jpeg', prog='sfdp')
    total = abs(start_time - int(time.time()))
    print(f'Done in {total}s!')
