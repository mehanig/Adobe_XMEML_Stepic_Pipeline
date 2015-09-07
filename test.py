import os
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


class TestProjectStructure(unittest.TestCase):

    def setUp(self):
        os.makedirs('testCoursePY/testEmptyLesson' )
        os.makedirs('testCoursePY/testLesson1/testStep1/Step1from999')
        os.makedirs('testCoursePY/testLesson1/testStep1/Step2from999')
        os.makedirs('testCoursePY/testLesson1/testStep2/Step3from1000')
        os.makedirs('testCoursePY/testLesson1/testStep3/Step1from1001')
        os.makedirs('testCoursePY/testLesson2/testStep3/Step3from1002')
        os.makedirs('testCoursePY/testLesson2/testStep4/Step3from1003')
        os.makedirs('testCoursePY/testLesson2/testStep4/Step6from1003')
        open('testCoursePY/testLesson1/testStep1/Step1from999/Step1from999_Screen.mp4', 'w').close() 
        open('testCoursePY/testLesson1/testStep1/Step1from999/Step1from999_Professor.mp4', 'w').close() 
        open('testCoursePY/testLesson1/testStep1/Step2from999/Step2from999_Screen.mp4', 'w').close() 
        open('testCoursePY/testLesson1/testStep1/Step2from999/Step2from999_Professor.mp4', 'w').close() 
        open('testCoursePY/testLesson1/testStep2/Step3from1000/Step3from1000_Screen.mp4', 'w').close() 
        open('testCoursePY/testLesson1/testStep2/Step3from1000/Step3from1000_Professor.mp4', 'w').close() 
        open('testCoursePY/testLesson1/testStep3/Step1from1001/Step1from1001_Screen.mp4', 'w').close() 
        open('testCoursePY/testLesson1/testStep3/Step1from1001/Step1from1001_Professor.mp4', 'w').close() 
        open('testCoursePY/testLesson2/testStep3/Step3from1002/Step3from1002_Screen.mp4', 'w').close() 
        open('testCoursePY/testLesson2/testStep3/Step3from1002/Step3from1002_Professor.mp4', 'w').close() 
        open('testCoursePY/testLesson2/testStep4/Step3from1003/Step3from1003_Screen.mp4', 'w').close() 
        open('testCoursePY/testLesson2/testStep4/Step3from1003/Step3from1003_Professor.mp4', 'w').close() 
        open('testCoursePY/testLesson2/testStep4/Step6from1003/Step6from1003_Screen.mp4', 'w').close() 
        open('testCoursePY/testLesson2/testStep4/Step6from1003/Step6from1003_Professor.mp4', 'w').close() 
        base_path = os.path.dirname(os.path.abspath(__file__))
        course_path =  os.path.join(base_path, 'testCoursePY')
        self.sequence_list = {'seq': {'testLesson1/testStep1': ['Step1from999', 'Step2from999'],
                                       'testLesson1/testStep2': ['Step3from1000'],
                                       'testLesson1/testStep3': ['Step1from1001'],
                                       'testLesson2/testStep3': ['Step3from1002'],
                                       'testLesson2/testStep4': ['Step3from1003', 'Step6from1003']},
                              'course_path': course_path}
    def tearDown(self):
        import shutil
        shutil.rmtree('testCoursePY')

    def test_folder_structure_is_in_format(self):
        self.assertTrue(os.path.isdir("testCoursePY"))
        validate_folder('testCoursePY')
        self.maxDiff = None
        gs = generate_sequence_list('testCoursePY', extra_path_lvl = 1)
        self.assertEqual(self.sequence_list['course_path'], os.sep + gs['course_path'])
        self.assertEqual(self.sequence_list['seq'], gs['seq'])

    def test_parse_course_bin_xml(self):
        parse_course_bin_xml('tests/test_cases/Algo_2015.xml')


    #No idea how to implement it(
    def test_Bin_object(self)
        pass
    
    
    def test_ffmpeg_duration_calculations(self):
        pass


if __name__ == '__main__':
    unittest.main()
