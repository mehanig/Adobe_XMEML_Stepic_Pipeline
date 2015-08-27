import unittest
from XMEMLops import *

class TestTemplateFile(unittest.TestCase):
    
    def setUp(self):
        self.media_xml = open('test_cases/example_media.xml', 'r')

    def tearDown(self):
        self.media_xml.close()

    def test_file_has_correct_content(self):
        pass

