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
        if re.match('(?s)<b.*?>(.*?)</b>', text):
            return re.match('(?s)<b.*?>(.*?)</b>', text).group(1).strip()
        else:
            return text

    def replace_character_codes(self, el):
        # Take an lxml element, replace unicode character codes for hyphens and non breaking spaces
        # and return a string with the replaced characters
        return string.replace(string.replace(lxml.etree.tostring(el), '&#160;', ' '), '&#173;', '-')

    def scrape_pdf(self):

        pdfdata = open(self.input, 'r').read()
        xmldata = scraperwiki.pdftoxml(pdfdata)

        self.data=[]
        namecount = 0
        sectioncount = -1
        intable = False
        currentsection = ''
        count = 0

        # Fontspecs are used to determine what content we're looking at.
        # These ids appear in the first content page when parsing the document.
        # Some years have more and different ids than others.
        # Setting the correct values is a trial and error apporach.
        # These ids can be obtained by running:
        # `./scrape_interests_pdf.py --input <filename>.pdf --print-font-ids=True`

        font_id_1 = '3'
        font_id_2 = '4'
        font_id_3 = '5'

        root = lxml.etree.fromstring(xmldata.encode('utf8'))
        pages = list(root)

        for page in pages:
            for el in list(page):
                element_text = ''
                count = count + 1
                if el.tag == "text":
                    text_element =  self.strip_bold(re.match('(?s)<text.*?>(.*?)</text>', self.replace_character_codes(el)).group(1))
                    if el.attrib['font'] == font_id_1:
                        # found a new MP
                        if len(self.data) == namecount:
                            self.data.append({})

                        self.data[namecount]['mp'] = text_element
                        namecount = namecount + 1

                    elif el.attrib['font'] == font_id_2 and re.match('[0-9]+[.] ([A-Z]+)', text_element):

                        # found new section
                        if text_element == '1. SHARES AND OTHER FINANCIAL INTERESTS':
                            sectioncount = sectioncount + 1
                        intable = False

                        currentsection = re.match('[0-9]{1,2}[.] (.*)', text_element).group(1)
                        self.data[namecount-1][currentsection] = {}

                    elif currentsection != '':
                        if text_element =='Nothing to disclose.':
                            self.data[namecount-1][currentsection] = text_element
                        elif not intable and el.attrib['font'] == font_id_3:
                            curtable = {}
                            intable = True
                            haverows = False
                            curtable[el.attrib['left']] = text_element
                            self.data[namecount-1][currentsection] = []
                            self.data[namecount-1][currentsection].append({})
                        elif intable and not haverows and text_element == ' ':
                            haverows = True
                        # Check this: we've stripped off the bold element
                        elif intable and not haverows and not re.match('(?s)<b.*?>(.*?)</b>', text_element) and el.attrib['font'] == font_id_3:
                            haverows = True
                        elif intable and not haverows:
                            curtable[el.attrib['left']] = text_element
                        elif intable and haverows and text_element == ' ':
                            if len(self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1]) > 0:
                                self.data[namecount-1][currentsection].append({})
                        elif intable and haverows:
                            if curtable[el.attrib['left']] in self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1]:
                                if self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]][-1] == ' ':
                                    self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] = self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] + text_element
                                else:
                                    self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] = self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] + ' ' + text_element
                            else:
                                self.data[namecount-1][currentsection][len(self.data[namecount-1][currentsection])-1][curtable[el.attrib['left']]] = text_element

    def write_results(self):
        with open(self.output, 'w') as outfile:
            json.dump({
                'year':self.year,
                'date': '%s-12-31' % (self.year),
                'source':self.source,
                'register':self.data},
            outfile,indent=1)

        pprint.pprint(self.data)

    def print_font_ids(self):
        pdfdata = open(self.input, 'r').read()
        xmldata = scraperwiki.pdftoxml(pdfdata)
        root = lxml.etree.fromstring(xmldata.encode('utf8'))
        pages = list(root)

        # Font ids we need are specified on first page that have interests.
        page_index = 1

        for el in list(pages[page_index]):
            if el.tag == "fontspec":
                print el.items()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape member's interests from pdf file")
    parser.add_argument('--input', help='Pdf file to scrape')
    parser.add_argument('--output', help='File to write json results to')
    parser.add_argument('--year', help='Year we are scraping')
    parser.add_argument('--source', help='Source of pdf file')
    parser.add_argument('--print-font-ids', help='Print the font ids used in the document')

    args = parser.parse_args()

    scraper = InterestScraper(args)

    if (args.print_font_ids):
        scraper.print_font_ids()
        exit()

    scraper.scrape_pdf()
    scraper.write_results()