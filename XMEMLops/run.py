import xml.dom.minidom as dom

from classes.BinNode import BinNode


def parse_course_bin_xml(xml_path):
    xml_course = dom.parse(xml_path)
    MainBin = BinNode(xml_course, mainNode=True)
    MainBin.parse()
    print("FINAL!")
    # MainBin.get_node_stat()
    MainBin.montage_by_steps()
    # MainBin.montage_by_one()
    MainBin.write_to_file()

if __name__ == '__main__':
    parse_course_bin_xml('Algo_2015_w3.xml')
