# -*- coding: utf-8 -*-

import os
import sys
import re
from copy import deepcopy
import xml.dom.minidom as dom
from xml.etree import ElementTree

DEFAULT_PROJECT_STRUTURE = { }
DEFAULT_SUBSTEP_NAME_PATTERN = r'^Step(?P<substep_id>[0-9]+)from(?P<step_id>[0-9]+)'
DEFAULT_SUBSTEP_FILES_PATTERN = r'^Step(?P<substep_id>[0-9]+)from(?P<step_id>[0-9]+)_(?P<postfix>Professor|Screen).'
NAME_REPLACEMENT_LIST = ['file', 'clipitem', 'sequence']
PARSED_NAMES = ['bin', 'clip', 'sequence']
POSTFIX_PROF = "_Professor.TS"
POSTFIX_SCREEN = "_Screen.mkv"
FILE_PATHURL_START = 'file:/'
NEW_FILE_POSTFIX = '_new.xml'

def openXMLSeqTemplate(path):
    try:
        return ElementTree.parse(path)
    except FileNotFoundError:
        raise RunTimeError('No Template File found')

def validate_folder(path):
    pass

def generate_sequence_list(path, extra_path_lvl=0):
    path = os.path.normpath(path)
    base_path = os.path.dirname(os.path.abspath(__file__))
    bpl = len(base_path.split(os.sep))
    bpel = os.path.dirname(sys.argv[0])
    if bpel == '':
        bpel = 0
    else:
        bpel = len(bpel.split(os.sep))
    base_path =os.path.join(*base_path.split(os.sep)[:bpl-bpel-extra_path_lvl])
    course_path = os.path.join(base_path, path)
    sequences = {'course_path': course_path, 'seq': {} }
    def update_seq(s, r, f):
        r = r.split(os.sep)
        l, stepName = r[-3:-1], r[-1]
        l = os.path.join(*l)
        if s['seq'].get(l): 
            if not stepName in s['seq'][l]:
                s['seq'][l].append(stepName)
        else:
            s['seq'].update({l: [stepName]})

    for root, dirs, files in os.walk(path):
        for f in files:
            if re.search(DEFAULT_SUBSTEP_NAME_PATTERN, f):
                update_seq(sequences, root, f)
    return sequences

# print_shift = 0
# tab = '____'

class BinNode(object):

    def __init__(self, node, name = None, parent = None ):
        if not name:
            self.name = node.nodeName
        self.parent = parent
        self.main = node
        self.children = []
        self.to_montage = []

    @staticmethod
    def _update_self_and_parents_with_montage(node, add_to_montage):
        if hasattr(node, 'parent') and node.parent:
            print('ADDING', add_to_montage)
            print(node.to_montage)
            BinNode._update_self_and_parents_with_montage(node.parent, add_to_montage)

        def make_unique(seq):
            seen = set()
            seen_add = seen.add
            return [ x for x in seq if not (x in seen or seen_add(x))]
        
        node.to_montage.append(add_to_montage)
        node.to_montage = make_unique(node.to_montage)
        
    def _update_nodes_to_montage(self, add_node):
        for cn in add_node.childNodes:
            m = None
            try:
                m = re.search(DEFAULT_SUBSTEP_FILES_PATTERN, cn.firstChild.nodeValue)
            except AttributeError:
                pass
            if cn.nodeName == 'name' and m: 
                print(m.group(0), cn.firstChild.nodeValue)
                BinNode._update_self_and_parents_with_montage(self, add_node)

    def parse(self):
        c = self.main.getElementsByTagName('children')
        children = None
        if c:
            children = c[0]
        if children:
            for n in children.childNodes:
                if n.nodeName in PARSED_NAMES:
                    self._update_nodes_to_montage(n)                            
 #                   global print_shift
 #                   print_shift += 1
                    
#                    print(tab*print_shift, n.nodeName)
                    newChild = BinNode(n, parent=self)
#                    print(print_shift * tab, 'parsing - >')
                    newChild.parse()
#                    print(print_shift * tab, '< - parsing')
#                    print_shift -= 1
                    self.children.append(n)
                    
                #                self.children.append(n)
#                print(n, n.nodeName, n.getElementsByTagName('name')[0].parentNode.nodeName, n.tagName)

    def get_node_stat(self):
        print(len(self.children))
        print(len(self.to_montage))
        print(len(set(self.to_montage)))
    
def parse_course_bin_xml(xml_path):
    xml_course = dom.parse(xml_path)
    MainBin = BinNode(xml_course)
    MainBin.parse()
    print("FINAL!")
    MainBin.get_node_stat()

def generate_template_from_list(tmplt, op_list, seqName = None):
    
    dom_f = dom.parse(tmplt)
    to_file = dom.parse(tmplt)
    
    def getAllTrackNodes(domfile):
        all_tracks = domfile.getElementsByTagName('track')
        return [t for t in all_tracks if len(t.getElementsByTagName('pathurl')) > 0]

    def construct_path(l):
        return os.sep.join(l)
    
    video_nodes = getAllTrackNodes(to_file) 
    for path, items in op_list['seq'].items():
        to_file.getElementsByTagName('name')[0].firstChild.nodeValue = str(items[0]) + '_Comp'
        for item in items:
            for name_node in to_file.getElementsByTagName('name'):
                if not name_node.firstChild or name_node.parentNode.nodeName not in NAME_REPLACEMENT_LIST:
                    continue
                name = name_node.firstChild.nodeValue
                postfix = name.split('_')[-1]
                name_node.firstChild.nodeValue = str(items[0]) + "_" + postfix
        
            for v in video_nodes:
                node = v.getElementsByTagName('pathurl')[0].firstChild
                new_path = construct_path([FILE_PATHURL_START, op_list['course_path'], str(path), str(item), str(item)])
                if node.nodeValue.endswith(POSTFIX_PROF):
                    node.nodeValue = new_path + POSTFIX_PROF
                elif node.nodeValue.endswith(POSTFIX_SCREEN):
                    node.nodeValue = new_path + POSTFIX_SCREEN
        name = str(item) + NEW_FILE_POSTFIX 
        target = open(name, 'w')
        to_file.writexml(target)
        target.close()


if __name__ == '__main__':
    x = generate_sequence_list('Algo2015Course')
    generate_template_from_list('example_media.xml', x)
    parse_course_bin_xml('Algo_2015_vSmal.xml')
    #print("X:", x)
