import unittest
import xml.dom.minidom as dom
from xml.etree import ElementTree
from XMEMLops import *

class LoadTemplateFile(unittest.TestCase):
    
    def setUp(self):
        self.media_xml = open('tests/test_cases/example_media.xml', 'r')

    def tearDown(self):
        self.media_xml.close()

    def test_file_has_correct_content(self):
        root = ElementTree.parse(self.media_xml).getroot()
        self.assertEqual(root.tag, 'xmeml')
        self.assertEqual(root.attrib['version'], '4')
    
    def test_loaded_file_match_version(self):
        tree = ElementTree.parse(self.media_xml).getroot()
        xml_tree = openXMLSeqTemplate('tests/test_cases/example_media.xml').getroot()
        self.assertEqual(ElementTree.tostring(tree),ElementTree.tostring(xml_tree))

if __name__ == '__main__':
    unittest.main()
