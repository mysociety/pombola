#!/usr/bin/env python

from bs4 import BeautifulSoup
from urlparse import urljoin
import sys
import json
import re
import unidecode


# where the original html came from, use to resolve relative urls
base_url = 'http://www.nassnig.org/nass/portfolio/profile.php'

# from http://stackoverflow.com/a/8366771/5349
def slugify(str):
    str = unidecode.unidecode(str).lower()
    return re.sub(r'\W+','-',str)


def process(filename):

    in_file = open( filename, 'r' )
    html = in_file.read()
    in_file.close()
    
    profile_url = urljoin( base_url, filename )
    
    soup = BeautifulSoup( html )
    content = soup.find('fieldset')
    # print soup.prettify()
        
    data     = {}
    raw_data = {}
    
    raw_data['name'] = content.find("p", "newsenn").get_text()
    
    # raw_data['email'] = content.find("td", height="21", colspan="2", valign="top" ).string
    
    
    img_url = content.find("img")["src"]
    raw_data['image'] = urljoin( base_url, img_url )
    
    for table_row in content.find_all('tr'):
    
        # print table_row.prettify()
    
        strong = table_row.find('strong')
        if not strong:
            continue 
    
        key = strong.string.strip().strip(':')
    
        sibling_cells = strong.find_parent('td').find_next_siblings()
        if not len( sibling_cells ): continue
    
        val = ''
        for sibling_cell in sibling_cells:        
            val = val + "\n" + sibling_cell.get_text("\n", strip=True)
        
        raw_data[key] = val.strip()
    
    # The education is listed in a different tr to the heading
    heading_tr = content.find('strong', text="Education:").find_parent('tr')
    content_tr = heading_tr.find_next_sibling('tr').find_all('td')[2]
    raw_data['Education'] = content_tr.get_text("\n", strip=True)
    
    
    # change the raw data to something more standard
    known_keys = [
        "Awards & Honours",
        "Committee(s) Membership", 
        "Date of Assumption",
        "Date of Birth", 
        "Education", 
        "Legistlative Experience", 
        "Legistlative Interest(s)", 
        "Marital Status", 
        "Senatorial District", 
        "Occupation", 
        "Political Party", 
        "Previous Appointments", 
        "Previous Elected Office", 
        "Seat Up Date", 
        "State", 
        "Target Achievement(s)", 
        "name",
        "email",
        "image",
    ]
    
    # Check that we don't have anything unexpected
    for key in raw_data.keys():
        if key not in known_keys:
            if not re.match('SEN', key): 
                raise Exception("Unknown key: " + key)
    
    # copy across basic bits
    name = raw_data['name']
    name = name.strip('SEN.').strip()
    name = re.sub( '\s+', ' ', name)
    data['name'] = name
    data['slug'] = slugify(name)
    
    # many are the same, could filter here
    # data['email'] = raw_data['email']
    
    data['image'] = raw_data['image']
    data['profile_url'] = profile_url
    
    data['date_of_birth'] = raw_data["Date of Birth"]
    
    data['positions'] = []
    
    data['positions'].append({
        "title":        'Senator',
        "organisation": 'Senate',
        "place":        raw_data["Senatorial District"],
        "start_date":   raw_data["Date of Assumption"],
        "end_date":     raw_data["Seat Up Date"],
        "type":         "political",
    })
    
    data['positions'].append({
        "title":        'Party Member',
        "organisation": raw_data["Political Party"],
        "type":         "political",    
    })
    
    for committee in raw_data["Committee(s) Membership"].split("\n"):
    
        original_line = committee
        is_chairman = re.search("Chairman", committee)
    
        if is_chairman:
            title = "Chairman"
            committee = re.sub("\s*\(?\s*Chairman\s*\)?\s*", "", committee)
        else:
            title = "Committee Member"
    
        data['positions'].append({
            "original_line": original_line,
            "title":         title,
            "organisation":  committee + ' Committee',
            "type":          "political",
        })
    
    
    for education in raw_data["Education"].split("\n"):
        education = re.sub("\d+\.\s", "", education)
        subtitle, year = re.match("(.*?)\s*(\d*)$", education).groups()
        data['positions'].append({
            "original_line": education,
            "title":         "Student",
            "subtitle":      subtitle,
            "organisation":  "",
            "end_date":      year,
            "type":          "education",
        })
    
    for office in raw_data["Previous Elected Office"].split("\n"):
        office = re.sub("\d+\.\s", "", office)
        data['positions'].append({
            "original_line": office,
            "title":         office,
            "organisation":  "",
            "type":          "political",
        })
        
    
    # Mop up rest into the summary
    summary = ''
    
    for key in ["Target Achievement(s)", "Legistlative Interest(s)", "Awards & Honours"]:
        if raw_data[key]:
            summary += key + ": " + raw_data[key] + "\n\n"
    
    data['summary'] = summary
    
    # print json.dumps( raw_data, sort_keys=True, indent=4 )
    # print json.dumps( data,     sort_keys=True, indent=4 )
    
    
    # write to file
    out = open( data['slug'] + '.json', 'w')
    out.write( json.dumps( data,     sort_keys=True, indent=4 ) )


for filename in sys.argv[1:]:
    print filename
    process( filename )
