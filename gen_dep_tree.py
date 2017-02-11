"""
1. read data, gen headers
2. save each resource in memeroy
3. build the tree

Limitations:
1. Can only deal with headers, can't handle PRIORITY or PUSH_PROMISE
2. Can't handle reprioritization.
"""

"""
t=12110666 [st=  633]    HTTP2_SESSION_SEND_HEADERS
                         --> exclusive = true
                         --> has_priority = true
:path: /static/css3two_blog/css/style.css
                         --> parent_stream_id = 0
                         --> stream_id = 3
                         --> weight = 256
"""
import re
import os
import pprint


pattern = r'(?P<key>[^\s]+)(: | = )(?P<value>[^\s]+)'
FRAME_HEADERS = 'HTTP2_SESSION_SEND_HEADERS'
PATH = ':path'
EXCLUSIVE = 'exclusive'
HAS_PRIORITY = 'has_priority'
PARENT_STREAM_ID = 'parent_stream_id'
STREAM_ID = 'stream_id'
WEIGHT = 'weight'


class PriorityTreeNode(object):

    def __init__(self, data):
        self.path = data.get(PATH)
        self.exclusive = data.get(EXCLUSIVE)
        self.has_priority = data.get(HAS_PRIORITY)
        self.parent_stream_id = data.get(PARENT_STREAM_ID)
        self.stream_id = data.get(STREAM_ID)
        self.weight = data.get(WEIGHT)
        self.parent = None
        self.children = []

    def __str__(self, level=0):
        ret = '  ' * level + repr(self) + '\n'
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret

    def __repr__(self):
        if self.path is None:
            path = 'root'
        elif self.path == '/':
            path = self.path
        else:
            path = os.path.basename(self.path)
        return 'resource:{0}, stream_id: {1}'.format(path, self.stream_id)


ROOT = PriorityTreeNode(data={STREAM_ID: '0'})


class PriorityTree(object):

    def __init__(self):
        self.root = ROOT
        self._map = {'0': ROOT}  # map id to node.

    def __str__(self):
        return str(self.root)

    @property
    def map(self):
        return self._map

    def add_node(self, stream_id, node):
        self._map[stream_id] = node


def gen_frame_data(filename):
    lines = open(filename).readlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i].strip()
        if line.endswith(FRAME_HEADERS):
            data = {}
            while True:
                i += 1
                line = lines[i].strip('-> ')
                match = re.search(pattern, line)
                if match:
                    data[match.group('key')] = match.group('value')
                else:
                    break
            yield data
        else:
            i += 1


def generate_dependency_tree(filename):
    nodes = [PriorityTreeNode(data) for data in gen_frame_data(filename)]
    tree = PriorityTree()
    for node in nodes:
        if node.stream_id not in tree.map:
            tree.add_node(node.stream_id, node)
            tree.map[node.parent_stream_id].children.append(node)
            node.parent = tree.map[node.parent_stream_id]
    print(tree)


if __name__ == '__main__':
    generate_dependency_tree('example-h2-session.txt')
