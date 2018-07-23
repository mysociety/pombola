import argparse

import scraperwiki
import lxml.etree
import re
import pprint
import json
import string

class InterestScraper(object):
    def __init__(self, args):
        self.input = args.input
        self.output = args.output
        self.year = args.year
        self.source = args.source

    def strip_bold(self, text):
        if re.match('(?s)<b.*?>(.*?)</b>',text):
            return re.match('(?s)<b.*?>(.*?)</b>',text).group(1)
        else:
            return text

    def scrape_pdf(self):

        pdfdata = open(self.input, 'r').read()
        xmldata = scraperwiki.pdftoxml(pdfdata)

        self.data=[]
        namecount=0
        sectioncount=-1
        intable=False
        currentsection=''

        root = lxml.etree.fromstring(xmldata.encode('utf8'))
        pages = list(root)

        count=0
        for page in pages:

            for el in list(page):
                count=count+1
                if el.tag == "text":
                    if el.attrib['font'] == '2':
                        # found a new MP
                        if len(self.data)==namecount:
                            self.data.append({})

                        self.data[namecount]['mp']=re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)
                        namecount=namecount+1
                    elif el.attrib['font'] == '3' and re.match('[0-9]+[.] ([A-Z]+)', self.strip_bold(re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1))):
                            #found new section
                            if re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)=='1. SHARES AND OTHER FINANCIAL INTERESTS ':
                                sectioncount=sectioncount+1
                            intable=False

                            currentsection=re.match('[0-9]{1,2}[.] (.*)',re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)).group(1)
                            self.data[namecount-1][currentsection]={}

                    elif currentsection!='':
                        if re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)=='Nothing to disclose.':
                            self.data[namecount-1][currentsection]=re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)
                        elif not intable and el.attrib['font'] == '3':
                            curtable={}
                            intable=True
                            haverows=False
                            curtable[el.attrib['left']]=re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)
                            self.data[namecount-1][currentsection]=[]
                            self.data[namecount-1][currentsection].append({})
                        elif intable and not haverows and re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)==' ':
                            haverows=True
                        elif intable and not haverows and not re.match('(?s)<b.*?>(.*?)</b>',re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)) and el.attrib['font'] == '5':
                            haverows=True
                        elif intable and not haverows:
                            curtable[el.attrib['left']]=re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)
                        elif intable and haverows and re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1)==' ':
                            if len(self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1])>0:
                                self.data[namecount-1][currentsection].append({})
                        elif intable and haverows:
                            if curtable[el.attrib['left']] in self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1]:
                                if self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]][-1]==' ':
                                    self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]]=self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]]+self.strip_bold(re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1))
                                else:
                                    self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]]=self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]]+' '+self.strip_bold(re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1))
                            else:
                                self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]]=self.strip_bold(re.match('(?s)<text.*?>(.*?)</text>', string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')).group(1))

    def write_results(self):
        with open(self.output, 'w') as outfile:
            json.dump({
                'year':self.year,
                'date': '%s-12-31' % (self.year),
                'source':self.source,
                'register':self.data},
            outfile,indent=1)

        pprint.pprint(self.data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape member's interests from pdf file")
    parser.add_argument('--input', help='Pdf file to scrape', required=True)
    parser.add_argument('--output', help='File to write json results to', required=True)
    parser.add_argument('--year', help='Year we are scraping', required=True)
    parser.add_argument('--source', help='Source of pdf file', required=True)

    args = parser.parse_args()

    scraper = InterestScraper(args)
    scraper.scrape_pdf()
    scraper.write_results()