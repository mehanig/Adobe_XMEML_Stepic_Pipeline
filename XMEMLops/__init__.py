from xml.etree import ElementTree

def openXMLSeqTemplate(path):
    try:
        return ElementTree.parse(path)
    except FileNotFoundError:
        raise RunTimeError('No Template File found')
