# -*- coding: utf-8 -*-
import re
from collections import defaultdict
import xml.dom.minidom as dom
from xml.etree import ElementTree
from classes.utils import calculate_duration, make_unique
from settings import *


def _new_prettify(content):
    reparsed = dom.parseString(content)
    return ('\n'.join([line for line in reparsed.toprettyxml(indent=' ' * 2).split('\n') if line.strip()]))


def shift_node_time(seq, ticks):
    for node in seq.getElementsByTagName('clipitem'):
        for el in node.getElementsByTagName('end'):
            el.firstChild.nodeValue = int(el.firstChild.nodeValue) + ticks
        for el in node.getElementsByTagName('start'):
            el.firstChild.nodeValue = int(el.firstChild.nodeValue) + ticks


# TODO: rewrite as class method?
# Add <clipitems> from seq2 <media> to appropriate <tracks>
def add_clip_to_end(seq1, seq2):
    end_max = 0
    for n in seq1.getElementsByTagName('end'):
        if end_max < int(n.firstChild.nodeValue):
            end_max = int(n.firstChild.nodeValue)

    shift_node_time(seq2, end_max)
    seq1_tracks = seq1.getElementsByTagName('track')
    seq2_tracks = seq2.getElementsByTagName('track')

    for e1, e2 in zip(seq1_tracks, seq2_tracks):
        for citem in e2.getElementsByTagName('clipitem'):
            new_citem = dom.parseString(_new_prettify(citem.toprettyxml())).documentElement
            e1.appendChild(new_citem)

# Main class for all nodes operation, based on assumption that project contains Bins.
class BinNode(object):
    def __init__(self, node, name=None, parent=None, mainNode=False):
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
            name = n.parentNode.getElementsByTagName('name')[0].firstChild.nodeValue
            print('name:', name)
            file_id = n.parentNode.attributes['id'].value
            path = n.firstChild.nodeValue
            duration = calculate_duration(path)
            self.file_links.update({name: [file_id, duration]})
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
                    BinNode(n, parent=self).parse()
                    self.children.append(n)

    # replaces ScreenCast and Video with appropriate version from file_links
    # Uniquify = replace <file id=...> and <masterclipid>...</> with apropriate values
    # replace <duration> with new calculated duration
    # integer !usually! is equal , file-33 is from masterclip-33 and so on
    def _uniquify_node_with_linked_files(self, node, linked_node_name):

        # files_pair_dict contains all linked files for node and looks like:
        # {'video': ['Step1from1303_Professor.mp4', ['file-97', 3075]], 'screen': ['Step1from1303_Screen.mp4', ['file-98', 3075]]}
        #
        files_pair_dict = {}
        name_start = linked_node_name.split('_')[0]
        for key, value in self.file_links.items():
            if (str(key)).startswith(name_start):
                if str(key).endswith(POSTFIX_PROF):
                    files_pair_dict.update({'video': [key, value]})
                elif str(key).endswith(POSTFIX_SCREEN):
                    files_pair_dict.update({'screen': [key, value]})

        print(files_pair_dict)
        node.getElementsByTagName('name')[0].firstChild.nodeValue = linked_node_name + '_COMP'
        for ci in node.getElementsByTagName('clipitem'):
            clip_type = 'video'
            if ci.getElementsByTagName('name')[0].firstChild.nodeValue.endswith(POSTFIX_SCREEN):
                clip_type = 'screen'

            for el in ci.getElementsByTagName('duration'):
                el.firstChild.nodeValue = files_pair_dict[clip_type][1][1]
            for el in ci.getElementsByTagName('end'):
                el.firstChild.nodeValue = files_pair_dict[clip_type][1][1]
            for el in ci.getElementsByTagName('out'):
                el.firstChild.nodeValue = files_pair_dict[clip_type][1][1]
            for el in ci.getElementsByTagName('name'):
                el.firstChild.nodeValue = linked_node_name + '_' + clip_type

            for el in ci.getElementsByTagName('file'):
                print(el.attributes['id'].value)
                el.setAttribute('id', files_pair_dict[clip_type][1][0])
                print('Replaced with ', el.attributes['id'].value)
                # go find parent which is <masterclip> and change it's id based on assumption that integers are same
                masterclip = el.parentNode.getElementsByTagName('masterclipid')[0]
                masterclip.firstChild.nodeValue = 'masterclip-' + el.attributes['id'].value.split('-')[-1]

    # Attach new seq nodes inside children of first bin and updates their data
    # For every folder with files will be 1 seq created
    # If needed to stuck substeps folder inside one step folder to one Seq use another method
    def montage_by_one(self):
        last_seq_id = int(self.seqTemplate.attributes['id'].value.split('-')[-1])
        main_bin = self.main.getElementsByTagName('bin')[0].getElementsByTagName('children')[0]
        for node in self.to_montage:
            last_seq_id += 1
            # linked_file_id = node.getElementsByTagName('file')[0].attributes['id'].value
            linked_node_name = node.getElementsByTagName('name')[0].firstChild.nodeValue
            print('node name:', linked_node_name)
            new_Seq = self.seqTemplate.cloneNode(deep=True)
            new_Seq.setAttribute('id', 'sequence-' + str(last_seq_id))
            self._uniquify_node_with_linked_files(new_Seq, linked_node_name)
            main_bin.appendChild(new_Seq)

    # Creates one sequence for 1 step folder based on subsptep_id
    def montage_by_steps(self):
        self.montage_by_one()
        substeps = defaultdict(dict)
        for n in self.main.getElementsByTagName('sequence'):
            name = n.getElementsByTagName('name')[0].firstChild.nodeValue
            m = re.search(DEFAULT_SUBSTEP_NAME_PATTERN, name)
            if m:
                step_id = int(m.group('step_id'))
                substep_id = int(m.group('substep_id'))
                substeps[step_id][substep_id] = n

        for index, substep_list in substeps.items():
            if len(substep_list.keys()) > 1:
                print(substep_list.keys())
                _sorted = sorted(substep_list)
                first, others = (_sorted[0], _sorted[1:])
                for key in others:
                    add_clip_to_end(substep_list[first], substep_list[key])

    # Workaround to delete emply lines after minidom.toprettyxml
    # Supports only UTF-8
    def write_to_file(self, name=None, path=None):
        if not name:
            name = str(self.name) + NEW_FILE_POSTFIX
        with open(name, 'w') as target:
            target.write(_new_prettify(self.main.toprettyxml()))

    def get_node_stat(self):
        print(len(self.children))
        print(len(self.to_montage))
        print(len(set(self.to_montage)))
        print(self.file_links)
