# -*- coding: utf-8 -*-

import os
import sys
import re
from copy import deepcopy
import xml.dom.minidom as dom
from xml.dom.minidom import parseString
from xml.etree import ElementTree

DEFAULT_PROJECT_STRUTURE = { }
DEFAULT_SUBSTEP_NAME_PATTERN = r'^Step(?P<substep_id>[0-9]+)from(?P<step_id>[0-9]+)'
DEFAULT_SUBSTEP_FILES_PATTERN = r'^Step(?P<substep_id>[0-9]+)from(?P<step_id>[0-9]+)_(?P<postfix>Professor|Screen).'
NAME_REPLACEMENT_LIST = ['file', 'clipitem', 'sequence']
PARSED_NAMES = ['bin', 'clip', 'sequence']
POSTFIX_PROF = "_Professor.TS"
POSTFIX_SCREEN = "_Screen.mp4"
FILE_PATHURL_START = 'file:/'
NEW_FILE_POSTFIX = '_new.xml'

def openXMLSeqTemplate(path):
    try:
        return ElementTree.parse(path)
    except FileNotFoundError:
        raise RunTimeError('No Template File found')

def validate_folder(path):
    pass

# generate data dict about course, finds lessons, course full path and steps
# key 'seq' contains another dictionary with keys - relative lesson paths from course path, 
# and values - list of step files
# First part with sys.args needed to split unnecessary parts of path, so we can run script
# from any folder "pyton3 Path/To/This/run.py CoursePath"
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

# Main class for all nodes operation, based on assumption that project contains Bins.
class BinNode(object):

    def __init__(self, node, name = None, parent = None, mainNode = False ):
        if not name:
            self.name = node.nodeName
        self.parent = parent
        self.main = node
        self.children = []
        self.to_montage = []
        self.seqTemplate = (node.getElementsByTagName('sequence') or [None])[0]
        self.file_links = {}
        if mainNode:
            self.create_file_links()

    # Recurcively updates nodes and parent nodes with to_montage information so every node
    # contain exact list of video substeps
    @staticmethod
    def _update_self_and_parents_with_montage(node, add_to_montage):
        if hasattr(node, 'parent') and node.parent:
            BinNode._update_self_and_parents_with_montage(node.parent, add_to_montage)

        def make_unique(seq):
            seen = set()
            seen_add = seen.add
            return [ x for x in seq if not (x in seen or seen_add(x))]
        
        node.to_montage.append(add_to_montage)
        node.to_montage = make_unique(node.to_montage)
        

    # Finds only nodes with name node and value of substep naming pattern
    def _update_nodes_to_montage(self, add_node):
        for cn in add_node.childNodes:
            try:
                nodeValue = cn.firstChild.nodeValue
            except AttributeError:
                continue
            m = re.search(DEFAULT_SUBSTEP_FILES_PATTERN, cn.firstChild.nodeValue)
            if cn.nodeName == 'name' and m: 
                BinNode._update_self_and_parents_with_montage(self, add_node)

    def create_file_links(self):
        for n in self.main.getElementsByTagName('pathurl'):
            print('YO')
            #print(n.parentNode.toprettyxml())
            name = n.parentNode.getElementsByTagName('name')[0].firstChild.nodeValue
            print(name)
            file_id = n.parentNode.attributes['id'].value
            self.file_links.update( {name : file_id})

    def parse(self):
        c = self.main.getElementsByTagName('children')
        children = None
        if c:
            children = c[0]
        if children:
            for n in children.childNodes:
                if n.nodeName in PARSED_NAMES:
                    self._update_nodes_to_montage(n)                            
                    newChild = BinNode(n, parent=self)
                    newChild.parse()
                    self.children.append(n)


    # replaces ScreenCast and Video with appropriate version from file_links
    def _uniquify_node_with_linked_files(self, node, linked_node_name):

        def get_screen_and_video_dict(linked_node_name):
            name_start = linked_node_name.split('_')[0]
            files_pair_dict = {}
            for key,value in self.file_links.items():
                if (str(key)).startswith(name_start):
                    if str(key).endswith(POSTFIX_PROF):
                        files_pair_dict.update({'video':[key, value]})
                    elif str(key).endswith(POSTFIX_SCREEN):
                        files_pair_dict.update({'screen': [key,value]})
            return files_pair_dict

        ops = get_screen_and_video_dict(linked_node_name)
        print(ops)
        node.getElementsByTagName('name')[0].firstChild.nodeValue = linked_node_name + '_COMP'
        for ci in node.getElementsByTagName('clipitem'):
            clip_type = 'video'
            if ci.getElementsByTagName('name')[0].firstChild.nodeValue.endswith(POSTFIX_SCREEN):
                clip_type = 'screen'
            for el in ci.getElementsByTagName('file'):
                print(el.attributes['id'].value)
                el.setAttribute('id', ops[clip_type][1])
                print('Replaced with ',el.attributes['id'].value)

    # Attach new seq nodes inside children of first bin and updates their data
    def montage(self):

        last_seq_id = int(self.seqTemplate.attributes['id'].value.split('-')[-1])
        main_bin = self.main.getElementsByTagName('bin')[0].getElementsByTagName('children')[0]
        for node in self.to_montage:
            last_seq_id += 1
            linked_file_id = node.getElementsByTagName('file')[0].attributes['id'].value
            linked_node_name = node.getElementsByTagName('name')[0].firstChild.nodeValue
            print('node name:', linked_node_name)
            new_Seq = self.seqTemplate.cloneNode(deep=True)
            new_Seq.setAttribute('id', 'sequence-' + str(last_seq_id))
            self._uniquify_node_with_linked_files(new_Seq, linked_node_name )
            main_bin.appendChild(new_Seq)

    
    # Workaround to delete emply lines after minidom.toprettyxml
    # Supports only UTF-8
    def write_to_file(self, path = None):
        
        def _new_prettify(content):
            reparsed = parseString(content)
            return('\n'.join([line for line in reparsed.toprettyxml(indent=' '*2).split('\n') if line.strip()]))

        name = str(self.name) + NEW_FILE_POSTFIX 
        with open(name, 'w') as target:
            target.write(_new_prettify(self.main.toprettyxml()))


    def get_node_stat(self):
        print(len(self.children))
        print(len(self.to_montage))
        print(len(set(self.to_montage)))
        print(self.file_links)
    

def parse_course_bin_xml(xml_path):
    xml_course = dom.parse(xml_path)
    MainBin = BinNode(xml_course, mainNode = True)
    MainBin.parse()
    print("FINAL!")
    MainBin.get_node_stat()
    MainBin.montage()
    MainBin.write_to_file()

# Based on sequence template, generate a lot of sequences with files from anothers steps
# Useless while this approach not reuse project files with linking inside project
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
    #x = generate_sequence_list('Algo2015Course')
    #generate_template_from_list('example_media.xml', x)
    parse_course_bin_xml('Algo_tests.xml')
    #print("X:", x)
