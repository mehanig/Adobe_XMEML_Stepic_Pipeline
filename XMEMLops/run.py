import xml.dom.minidom as dom
import click
from classes.BinNode import BinNode


@click.command()
@click.option('-i', help='Path to XML template file')
@click.option('-o', help='Output file')
def parse_course_bin_xml(i, o):
    xml_course = dom.parse(i)
    MainBin = BinNode(xml_course, mainNode=True)
    MainBin.parse()
    print("FINAL!")
    print(o)
    # MainBin.get_node_stat()
    MainBin.montage_by_steps()
    # MainBin.montage_by_one()
    MainBin.write_to_file()

if __name__ == '__main__':
    parse_course_bin_xml()
