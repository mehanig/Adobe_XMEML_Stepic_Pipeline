# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
from collections import defaultdict
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
FFPROBE_RUN_PATH = 'ffprobe'
DUMBPREFIX = 'file://localhost'
PROJECT_TIMEBASE = 25
TEXT_NODE = 3

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


#run ffprobe and returns number of frames
def calculate_duration_in_sec(path):
    filepath = path[len(DUMBPREFIX):]
    print(filepath)
    result = subprocess.Popen([FFPROBE_RUN_PATH, filepath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration_string = [x.decode("utf-8") for x in result.stdout.readlines() if "Duration" in x.decode('utf-8')][-1]
    time = duration_string.replace(' ', '').split(',')[0].replace('Duration:', '').split(':')
    return int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2].split('.')[0])

def get_frame_count(path):
    filepath = path[len(DUMBPREFIX):]
    result = subprocess.Popen([FFPROBE_RUN_PATH, '-select_streams', 'v', '-show_streams', filepath],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    frames = [x.decode("utf-8") for x in result.stdout.readlines() if "avg_frame_rate=" in x.decode('utf-8')][0]
    return PROJECT_TIMEBASE
    #return 25
    #return int(frames.split('=')[-1].split('/')[0])

def calculate_duration(path):
    return calculate_duration_in_sec(path)*get_frame_count(path)


def _delete_text_nodes(nodelist):
    return [x for x in nodelist if x.nodeType != 3]


def _new_prettify(content):
    reparsed = parseString(content)
    return('\n'.join([line for line in reparsed.toprettyxml(indent=' '*2).split('\n') if line.strip()]))


# TODO: rewrite as class method?
#Add clipnodes from seq2 <media> to end of seq1 media
def add_clip_to_end(seq1, seq2):
    end_max = 0
    for n in seq1.getElementsByTagName('end'):
        if end_max < int(n.firstChild.nodeValue):
            end_max = int(n.firstChild.nodeValue)

    for ch in _delete_text_nodes(seq2.getElementsByTagName('media')[0].childNodes):
        print('appending', ch.getElementsByTagName('name')[0].firstChild.nodeValue)
        # TODO is new_ch needed??
        new_ch = dom.parseString(_new_prettify(ch.toprettyxml())).documentElement
        seq1.getElementsByTagName('media')[0].appendChild(new_ch)

#    for ch in _delete_text_nodes(seq2.getElementsByTagName('track')):

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
    # To avoid duplicates we only add half of nodes to montage (thouse which are not Screencasts)
    def _update_nodes_to_montage(self, add_node):
        for cn in add_node.childNodes:
            # We go through all nodes, which isn't optimal solution
            # Can be rewritten
            try:
                nodeValue = cn.firstChild.nodeValue
            except AttributeError:
                continue
            m = re.search(DEFAULT_SUBSTEP_FILES_PATTERN, cn.firstChild.nodeValue)
            if cn.nodeName == 'name' and m:
                if cn.firstChild.nodeValue.endswith(POSTFIX_SCREEN):
                    BinNode._update_self_and_parents_with_montage(self, add_node)

    # file_links = {'name': ['file_id', 'duration']}
    def create_file_links(self):
        for n in self.main.getElementsByTagName('pathurl'):
            #print(n.parentNode.toprettyxml())
            name = n.parentNode.getElementsByTagName('name')[0].firstChild.nodeValue
            print('name:', name)
            file_id = n.parentNode.attributes['id'].value
            path = n.firstChild.nodeValue
            #print('path', path)
            duration = calculate_duration(path)
            self.file_links.update( {name : [file_id, duration]}) 
            print(duration)
            

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
    # Uniquify = replace <file id=...> and <masterclipid>...</> with apropriate values
    # replace <duration> with new calculated duration
    # integer !usually! is equal , file-33 is from masterclip-33 and so on
    
    def _uniquify_node_with_linked_files(self, node, linked_node_name):

        def get_screen_and_video_dict(linked_node_name):
            name_start = linked_node_name.split('_')[0]
            files_pair_dict = {}
            for key,value in self.file_links.items():
                if (str(key)).startswith(name_start):
                    if str(key).endswith(POSTFIX_PROF):
                        files_pair_dict.update({'video':[key, value]})
                    elif str(key).endswith(POSTFIX_SCREEN):
                        files_pair_dict.update({'screen': [key, value]})
            return files_pair_dict

        ops = get_screen_and_video_dict(linked_node_name)
        print(ops)
        node.getElementsByTagName('name')[0].firstChild.nodeValue = linked_node_name + '_COMP'
        for ci in node.getElementsByTagName('clipitem'):
            clip_type = 'video'
            if ci.getElementsByTagName('name')[0].firstChild.nodeValue.endswith(POSTFIX_SCREEN):
                clip_type = 'screen'
            for el in ci.getElementsByTagName('duration'):
                el.firstChild.nodeValue = ops[clip_type][1][1]
            for el in ci.getElementsByTagName('end'):
                el.firstChild.nodeValue = ops[clip_type][1][1]
            for el in ci.getElementsByTagName('out'):
                el.firstChild.nodeValue = ops[clip_type][1][1]
            for el in ci.getElementsByTagName('name'):
                el.firstChild.nodeValue = linked_node_name 

            for el in ci.getElementsByTagName('file'):
                print(el.attributes['id'].value)
                el.setAttribute('id', ops[clip_type][1][0])
                print('Replaced with ',el.attributes['id'].value)
                # go find parent which is <masterclip> and change it's id based on assumption that integers are same
                el.parentNode.getElementsByTagName('masterclipid')[0].firstChild.nodeValue = 'masterclip-' + el.attributes['id'].value.split('-')[-1]

    # Attach new seq nodes inside children of first bin and updates their data
    # For every folder with files will be 1 seq created
    # If needed to stuck substeps folder inside one step folder to one Seq use another method
    def montage_by_one(self):

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

    # Creates one sequence for 1 step folder based on subsptep_id 
    def montage_by_steps(self):
    
        def _getId(_tuple):
            return _tuple[0]

        self.montage_by_one()
        substeps = defaultdict(dict)
        for n in self.main.getElementsByTagName('sequence'):
            name = n.getElementsByTagName('name')[0].firstChild.nodeValue
            m = re.search(DEFAULT_SUBSTEP_NAME_PATTERN, name)
            if m:
                step_id = int(m.group('step_id'))
                substep_id = int(m.group('substep_id'))
                print('IMAPPENDING', step_id, substep_id, n )
                substeps[step_id].update({substep_id :n })
    
        for index, substep_list in substeps.items():
            if len(substep_list.keys()) > 1:
                print(index)
                print(sorted(substep_list.keys())
                for key in sorted(substep_list.keys()):
                    print('ADDIND',substep_list[key])
                    add_clip_to_end(substep_list[key], substep_list[key])
    # Workaround to delete emply lines after minidom.toprettyxml
    # Supports only UTF-8

    # Workaround to delete emply lines after minidom.toprettyxml
    # Supports only UTF-8
    def write_to_file(self, path = None):
        
        name = str(self.name) + NEW_FILE_POSTFIX 
        with open(name, 'w') as target:
            target.write(_new_prettify(self.main.toprettyxml()))


    def get_node_stat(self):
        print(len(self.children))
        print(len(self.to_montage))
        print(len(set(self.to_montage)))
        print(self.file_links)


class StepMontageStruct(object):
    
    def __init__(self, id, seqnode):
        self.montage = [(id,seqnode)]

    def _getId(self, _tuple):
        return _tuple[0]

    def add(self, id,seqnode):
        self.montage.append((id,seqnode))
        self.montage = sorted(self.montage, key = self._getId)

def parse_course_bin_xml(xml_path):
    xml_course = dom.parse(xml_path)
    MainBin = BinNode(xml_course, mainNode = True)
    MainBin.parse()
    print("FINAL!")
    MainBin.get_node_stat()
    MainBin.montage_by_steps()
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
