#!  /usr/bin/python3

# removes direct formating from the content.xml file of an odt document
# by removing the Txxx and OOoDefault styles (if they exist)
# not all Txxx styles are removed

# Author Milos Sramek milos.sramek@soit.sk
# Use as you wish, without warranty

import sys, getopt, os, shutil,re
import zipfile

from lxml import etree
from io import StringIO
from copy import deepcopy
import sys, getopt, tempfile
import ipdb
#ipdb.set_trace()

def isP(item):
    #if item.tag[-2:]=='}p':
    if item.tag[-2:]=='}p' or item.tag[-2:]=='}h':
        return True
    else:
        return False

def isH(item):
    if item.tag[-2:]=='}h':
        return True
    else:
        return False

def isFrame(item):
    if item.tag[-6:]=='}frame':
        return True
    else:
        return False

def hasText(item):
    if     item.text == None: 
        return False
    else:
        return True


def getSpanType(item):
    """
    chect if item is span, but not T-span
    """
    if item.tag.find('span') >= 0:
        for key in list(item.keys()):
            if key.find('style-name') >=0 :
                return item.attrib[key]
    return None

def isNotXXSpan(item, txtId):
    """
    chect if item is span, but not txtId-span
    """
    if item.tag.find('span') >= 0:
        for key in list(item.keys()):
            if key.find('style-name') >=0 :
                if item.attrib[key].find(txtId) != 0 : return True
    return False

def isNotTSpan(item):
    """
    chect if item is span, but not T-span
    """
    if item.tag.find('span') >= 0:
        for key in list(item.keys()):
            if key.find('style-name') >=0 :
                if item.attrib[key].find('T') != 0 : return True
    return False

def isNotODSpan(item):
    """
    chect if item is span, but not T-span
    """
    if item.tag.find('span') >= 0:
        for key in list(item.keys()):
            if key.find('style-name') >=0 :
                if item.attrib[key].find('OOoDefault') != 0 : return True
    return False

def isRemovableTSpan(item):
    if isTSpan(item) and len(item.getchildren()) == 0 and item.tail == None:
        return True
    else:
        return False

def isSpan(item):
    return item.tag.find('span') >= 0

def isXXSpan(item, txt):
    if item.tag.find('span') >= 0:
        for key in list(item.keys()):
            if key.find('style-name') >=0 :
                if item.attrib[key].find(txt) == 0 : return True
    return False

def hasFrameChild(item):
    for i in item.getchildren():
        if isFrame(i):
            return True
    return False

def isSimpleTag(item):
    """
    a tag is 'simple' if it has no tail or children
    """
    return not (item.tail or len(item.getchildren()))

def isTSpan(item):
    """
    check if span is 'Txxx' 
    """
    return isXXSpan(item, 'T')

def isODSpan(item):
    """
    check if span is 'OOoDefault'
    """
    return isXXSpan(item, 'OOoDefault')

def isOMPSpan(item):
    """
    check if span is 'OOoMenuPath'
    """
    return isXXSpan(item, 'OOoDefault')

def ODtoTSpans(tree):
    """
    Change OOoDefault spanst to T spans
    """
    for iitem in tree.xpath('//*'):
        if isODSpan(iitem):
            item = deepcopy(iitem)
            for key in list(item.keys()):
                if key.find('style-name') >= 0 :
                    print(item.attrib[key], end=' ')
                    item.attrib[key] = 'T1'
                    print(item.attrib[key])
            iitem.getparent().replace(iitem, item)

def mergeSameSpans(tree):
    """
    Merge consecutive spans with the same style-name
    """
    for iitem in tree.xpath('//*'):
        if isP(iitem) and iitem.getchildren():
            if len(iitem.getchildren()) > 1:
                item = deepcopy(iitem)
                elist = list(item)
                prevSpanType = None
                prevItem = elist[0]
                if isSimpleTag(prevItem): prevSpanType = getSpanType(prevItem)
                for el in elist[1:]:
                    if isSpan(el) and (not el.getchildren()) and getSpanType(el) == prevSpanType:
                        if el.text and prevItem.text:
                            prevItem.text = prevItem.text + el.text
                        elif el.text:
                            prevItem.text = el.text
                        # if e.tail exists, assign it to the previous span 
                        # and restart span search
                        if el.tail: 
                            prevItem.tail = el.tail
                            prevSpanType = None
                        item.remove(el)
                    else:
                        prevItem = el
                        prevSpanType = None
                        if isSimpleTag(prevItem): prevSpanType = getSpanType(prevItem)
                iitem.getparent().replace(iitem, item)

def mergeSameChildren(tree):
    """
    Merge children, if they have the same span style-name
    """
    for iitem in tree.xpath('//*'):
        if isSpan(iitem):
            item = deepcopy(iitem)
            if len(item.getchildren()) == 1 and item.tail == None:
                child = item.getchildren()[0]
                if getSpanType(item) == getSpanType(child):
                    if item.text and child.text:
                        item.text = item.text + child.text
                    elif elist[el].text:
                        item.text = child.text
                    item.remove(child)
            iitem.getparent().replace(iitem, item)

def cleanSpans(tree, txtId, verbose=False):
    """
    remove T spans if they are the only child of some other span which does not have text
    """
    for iitem in tree.xpath('//*'):
        if isNotXXSpan(iitem, txtId):
            item = deepcopy(iitem)
            elist = list(item)
            if len(elist) == 1 and isTSpan(elist[0]) and item.text == None: 
                child = elist[0]
                #if isTSpan(child) and len(child.getchildren()) == 0:
                if isRemovableTSpan(child):
                    item.text = child.text
                    item.remove(child)
                    if verbose: pitem(item, 'cleanSpans('+txtId+')')
            iitem.getparent().replace(iitem, item)

def remTSpans(tree, verbose=False):
    """
    not working
    replace T spans if they only one child by the child
    """
    for iitem in tree.xpath('//*'):
        if isTSpan(iitem):
            elist = list(iitem)
            if len(elist) == 1:
                iitem.getparent().replace(iitem, deepcopy(elist[0]))

def pitem(item, txt=''):
    print(txt,':', '{',item.text,'}', end=' ')
    for it in list(item):
        #print it.tag, '{',it.text,'|', it.tail,'}',
        print('{',it.text,'|', it.tail,'}', end=' ')
    print()

def mergeSpans(tree, txtId, verbose=False):
    """
    Merge consecutive spans with text:style-name=txtId and remove the span
    Drawback: may corrupt direct formatting (which is done by Txx spans)
    """
    for iitem in tree.xpath('//*'):
        # frame in paragraph may cause problems...
        #if isP(iitem) and not hasFrameChild(iitem):
        if isP(iitem):
            #for i in iitem.getchildren(): print i.tag
            item = deepcopy(iitem)
            changed = True
            changes = 0
            while changed:
                #pitem(item)
                changed = False
                elist = list(item)
                for el in range(len(elist)):
                    #print 'P: ', el
                    if isXXSpan(elist[el], txtId) and len(elist[el].getchildren()) == 0:
                        etext=''
                        etail=''
                        if elist[el].text: etext = elist[el].text
                        if elist[el].tail: etail = elist[el].tail
                        if el == 0:    #append to patent's text
                            if item.text:
                                item.text = item.text + etext + etail
                            else:
                                item.text = etext + etail
                        else:    #append to previous item's text
                            eetail=''
                            if elist[el-1].tail: 
                                eetail = elist[el-1].tail
                            elist[el-1].tail = eetail + etext + etail
                        item.remove(elist[el])
                        changed = True
                        changes += 1
                        break
            #if verbose and changes > 0: pitem(item, 'mergeSpans('+txtId+')')

            #ipdb.set_trace()
            parent = iitem.getparent()
            #for iii in parent.getchildren(): print "X", pitem(iii)
            parent.replace(iitem, item)
            #for iii in parent.getchildren(): print "Y", pitem(iii)


def usage():
    print("Remove direct character formatting and the OOoDefault spans")
    print("from an odt document")
    print("Usage: ",sys.argv[0]+ " -i ifile.odt -o ofile.odt")

def parsecmd():
    global iname, oname
    try:
        opts, Names = getopt.getopt(sys.argv[1:], "hi:o:", [])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        usage(desc)
        sys.exit(2)
    for o, a in opts:
        if o in ("-o"):
            oname = a
        elif o in ("-i"):
            iname = a
        elif o in ("-h"):
            usage()
            sys.exit(0)
        else:
            assert False, "unhandled option"

def removeInFile(fname, tag):
    # parse the 'content.xml' file and clean up
    tree = etree.parse(fname)
    #root = tree.getroot()
    #not working remTSpans(tree)
    mergeSpans(tree, tag, verbose)
    cleanSpans(tree, tag, verbose)
    mergeSameSpans(tree)
    tree.write(fname)

def removeInFileRE(fname, tags):
    # parse the 'content.xml' file and clean up
    with open(fname) as ifile:
        text=ifile.read()

    #text='<text:p text:style-name="LibOTextkörper"><text:span text:style-name="LibOStandard">Dieses Dokument unterliegt dem Copyright © 201</text:span><text:span text:style-name="LibOStandard"><text:span text:style-name="T54">4</text:span></text:span><text:span text:style-name="LibOStandard">. Die Beitragenden sind unten aufgeführt. Sie dürfen dieses Dokument unter den Bedingungen der GNU General Public License (</text:span><text:a xlink:type="simple" xlink:href="http://www.gnu.org/licenses/gpl.html" text:style-name="Internet_20_link" text:visited-style-name="Visited_20_Internet_20_Link"><text:span text:style-name="LibOStandard">http://www.\xadgnu.org/licenses/gpl.html</text:span></text:a><text:span text:style-name="LibOStandard">), Version 3 oder höher, oder der </text:span><text:span text:style-name="LibOStandard"><text:span text:style-name="T2">Creative Commons Attribution License</text:span></text:span><text:span text:style-name="LibOStandard"> (</text:span><text:a xlink:type="simple" xlink:href="http://creativecommons.org/licenses/by/3.0/" text:style-name="Internet_20_link" text:visited-style-name="Visited_20_Internet_20_Link"><text:span text:style-name="LibOStandard">http://creativecommons.org/licenses/by/3.0/</text:span></text:a><text:span text:style-name="LibOStandard">), Version 3.0 oder höher, verändern und/oder weitergeben.</text:span></text:p>'

    text = re.sub(r'<text:span text:style-name="T[0-9]*">([^<]*)</text:span>',r'\1', text)
    text = re.sub(r'<text:span text:style-name="T[0-9]*">([^<]*<text:line-break/>[^<]*)</text:span>',r'\1', text)
    for tag in tags:
        pass
        #ipdb.set_trace()
        text = re.sub(r'<text:span text:style-name="%s">([^<]*)</text:span>'%tag,r'\1',text)
        text = re.sub(r'<text:span text:style-name="%s">([^<]*<text:line-break/>[^<]*)</text:span>'%tag,r'\1',text)
    text = re.sub(r'<text:span text:style-name="T[0-9]*">([^<]*<text:line-break/>[^<]*)</text:span>',r'\1', text)
    with open(fname, "w") as ifile:
        ifile.write(text)

oname = 'ofile.odt'
iname = 'ifile.odt'
parsecmd()
tmpdir=tempfile.mkdtemp()
verbose=True #

# directory to extract th eodt file to
actdir=os.getcwd()
if not os.path.isabs(iname):
    iname = actdir+'/'+iname
if not os.path.isabs(oname):
    oname = actdir+'/'+oname

#extract the document
with zipfile.ZipFile(iname, "r") as z:
    z.extractall(tmpdir)

# remove output, if exists. Otherwise the zip routine would update it
if os.path.isfile(oname):
    os.remove(oname)

#open the output document - zip file
zf = zipfile.ZipFile(oname, "w")

#ennter the directory with the extracted document
os.chdir(tmpdir)

removeInFileRE('content.xml', ['LibOStandard', 'Character_20_style'])
removeInFile('content.xml', 'T') 
removeInFile('content.xml', 'T') 
removeInFile('content.xml', 'Character_20_style')
removeInFile('content.xml', 'Character_20_style')
removeInFile('content.xml', 'LibOStandard')
removeInFile('content.xml', 'LibOStandard')

#os.system('zip -r '+oname+' *')
# save the modified document
for dirname, subdirs, files in os.walk('.'):
    for filename in files:
        zf.write(os.path.join(dirname, filename))
zf.close()

#return back and remove the extracted document
os.chdir(actdir)
shutil.rmtree(tmpdir)
