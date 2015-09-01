# -*- coding: utf-8 -*-

import os
import sys
import re
from copy import deepcopy
import xml.dom.minidom as dom
from xml.etree import ElementTree

DEFAULT_PROJECT_STRUTURE = { }
DEFAULT_SUBSTEP_NAME_PATTERN = r'^Step(?P<substep_id>[0-9]+)from(?P<step_id>[0-9]+)'
NAME_REPLACEMENT_LIST = ['file', 'clipitem', 'sequence']
POSTFIX_PROF = "_Professor.TS"
POSTFIX_SCREEN = "_Screen.TS"
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
    print("X:", x)
