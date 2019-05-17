## mapper.py - a python script to graph minecraft datapacks (1.13/1.14)

This script will generate a graph jpeg where each node is a function file and each connection is it's call to another function. You can use this script to map out your datapack and figure out what's going on.

## Code Example

* `python mapper.py mydatapack`
* `python mapper.py mydatapack myotherdatapack`
* `python mapper.py mydatapack -o output`
* `python mapper.py mydatapack --label`

*your setup may require python3 instead of python*

## Examples

Default
![example](https://raw.githubusercontent.com/RitikShah/mapper/master/example.jpeg)

With Labels
![example](https://raw.githubusercontent.com/RitikShah/mapper/master/example_labeled.jpeg)

## Motivation

The purpose of this project was to understand medium to large datapacks and see where the components lie and how the different systems connect. The purpose is to also spot potential optimizations in rather large datapacks by enabling labeling.

## Dependencies

This script relies on a dependancy called !graphviz[https://www.graphviz.org/] and the python hooks, pygraphviz.
graphviz is a C++ library so it requires the C++ tools to be able to run it (Mac: XCode, Win: Microsoft C++ Distributables)

Before using the script, install !pygraphviz[https://pypi.org/project/pygraphviz/]:
`pip install pygraphviz` - this should handle all of it

*again pip3 might be necessary*

## Script

After setting up the dependencies, just download the mapper.py script and place it outside your datapacks (you can place it in your mc datapack folders if you like, just not inside them)

## Usage

This script comes with minor tweaking options but the main usage is as follows:
`python mapper.py <datapack> [anotherdatapack ...]`

Running: `python mapper.py -h` will pull up a help menu describing the other options
* `datapack [datapack2 datapack 3 ...]` include datapack(s) for the tool to be used on
* `-m --mode MODE` will set the mode:
  * * default is `one` where all the datapacks will output to one graph
  * * `multiple` is where the datapacks output to their own graphs
* `-l --label` will enabling labeling. This includes what you called each function with on the line connecting nodes
* `-o --outfile OUTFILE` will allow you to name your own output file. for `multiple` mode, this is ignored

## Tests

Maybe in the future, hehe

## Notes

This script is pretty fragile so only feed it valid datapacks. It also doesn't handle zip files yet, so watch the page if you are interested in that.

I have some more things planned, but for now, it's just this.

I'm on discord as @rx#1284 

## License

MIT
