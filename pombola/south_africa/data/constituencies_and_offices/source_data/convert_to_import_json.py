# *-* coding: utf-8
# Converts constituency files received from parties to the json format
# suitable for import. The intention is to minimise manual editing,
# although this is unavoidable.

# For ANC files the major change made is remove PLOs (Parliamentary
# Liason Officers) of ministers as they are understood to be government,
# not party officials and there is no clear way to include them in
# Pombola at present (although this should be addressed in the future).

# Other parties' processed files have been manually restructured into
# the structure seen by this script.

# This script should be updated for each set of data received.

# Last updated: January 2015.

import distutils.spawn
import subprocess
import re
import json
import csv


def ensure_executable_found(name):
    if not distutils.spawn.find_executable(name):
        raise ImproperlyConfigured("Can't find executable '{0}' which is needed by this code".format(name))

manual_name_corrections = {
    'Morutoa Rosalia Masefele Story': 'Masefele Rosalia Morutoa',
    'Mike Masutha': 'Michael Masutha',
    'Sibongiseni Mchunu': 'Sibongile Mchunu',
    'Omie Singh': 'Aumsensingh Singh',
    'Nathi Nhleko': 'Nkosinathi Nhleko',
    'Zet Luzipho': 'Sahlulele Luzipho',
    'Nonzwakazi Swartbooi': 'Gloria Nonzwakazi Swartbooi-Ntombela',
    'Emmanuel Kebby Maphotse': 'Kebby Maphatsoe',
    'Dipuo Letsatsi': 'Dipuo Bertha Letsatsi-Duba',
    'Thoko Didiza': 'Angela Thokozile Didiza',
    'Koena Mmanoko Elisabeth Masehela': 'Elizabeth Koena Mmanoko Masehela',
    'Ishmael Kgetjepe': 'Maaria Ishmael Kgatjepe',
    'Clara Dikgale': 'Masefako Clarah Dikgale',
    'Sheila Sithole-Shope': 'Sheila Coleen Nkhensani Shope-Sithole',
    'DD Mabuza': 'David Dabede Mabuza',
    'Pat Sibande': 'Mtikeni Patrick Sibande',
    'Timothy Khoza': 'Timothy Zanoxolo Matsebane Khoza',
    'Simon P Skhosana': 'Piet Simon Skhosana',
    'Friedah Nkadimeng': 'Mogotle Friddah Nkadimeng',
    'Cathy Dlamini': 'Landulile Cathrine Dlamini',
    'Vusi R. Shongwe': 'Vusumuzi Robert Shongwe',
    'Dudu Manana': 'Duduzile Promise Manana',
    'Thandi B Shongwe': 'Blessing Thandi Shongwe',
    'Rosinah Semenye': 'Machwene Rosina Semenya',
    'Pinky Phosa': 'Yvonne Nkwenkwezi Phosa',
    'Busi Coleman': 'Elsie Mmathulare Coleman',
    'Jabu Mahlangu': 'Jabulani Lukas Mahlangu',
    'Rhodah Mathebe': 'Rhoda Sazi Mathabe',
    'Motlashuping Msosa': 'Tekoetsile Consolation Motlashuping',
    'Tumi Moiloa': 'Boitumelo Theodora Moiloa',
    'Jeanette Nyathi': 'Ntebaleng Jeannete Nyathi',
    'Johni Steenkamp': 'Johanna Steenkamp',
    'Leon Basson': 'Leonard Jones Basson',
    'Manuel Simao De Freitas': 'Manuel Simão Franca De Freitas',
    'Anroux Johanna Marais': 'Anroux Johanna Du Toit Marais',
    'Elizabeth Van Lingen': 'Elizabeth Christina Van Lingen',
    'Belinda Bozzoli (Van Onselen)': 'Belinda Bozzoli',
    'Philly Mapulane': 'Mohlopi Phillemon Mapulane',
    'Kenny Mmoiemang': 'Mosimanegare Kenneth Mmoiemang',
    'Natasha Elsbe Louw': 'Elsabe Natasha Louw',
    'Fana Mokoena': 'Lehlohonolo Goodwill Mokoena',
    'Modikela Mathloko': 'Abinaar Modikela Matlhoko',
    'Mpho Ramakatsa': 'Ramakaudi Paul Ramakatsa',
    'Veronica Mente-Nqweniso': 'Ntombovuyo Veronica Nqweniso',
    'Asanda Matshobane': 'Asanda Matshobeni',
    'Zwelivelile Mandlesizwe Dalibhunga': 'Zwelivelile Mandlesizwe Dalibhunga Mandela',
    'Jacob Marule': 'Marule Otto Jacob',
    'Jack Matlala': 'Matlala Jack Lesiba',
    'Regina Mhawule': 'Makgabo Reginah Mhaule',
    'David Dube': 'Boy David Dube',
    'Hlomane Chauke': 'Hlomane Patrick Chauke',
    'Zoleka Capa-Langa': 'Zoleka Capa',
    'Henro Kruger': 'Hendrika Johanna Lodiwika Kruger',
    'Bob Mabaso': 'Xitlhangoma Mabasa',
    'Mtsi Alfred': 'Skuta Alfred Mtsi',
    'VV Windvoel': 'Victor Vusumuzi Zibuthe Windvoël',
    'Suzan Dantjie': 'Sussana Rebecca Tsebe',
    'Vauda': 'Younus Cassim Vawda',
    'Basson, Catherine': 'Catherine Basson',
    'Feni, Hegrico': 'Hegrico Feni',
    'Jack, Sizwe': 'Sizwe Jack'

}

manual_location_corrections = {
    '48 Chaplain Street, Ngqeleni, 5140 (R63, Port St Johns Road)': 'Ngqeleni',
    'Kuyga Comm. Hall, Green bushes, 6390': 'Greenbushes, Port Elizabeth, Eastern Cape',
    'Nyandeni Municipality, Libode Town Hall, 5160': 'Libode',
    '1 Main Street, Wilton Mkwayi Street, Middle drift, 5685(opposite SAPS)': 'SAPS, Middledrift',
    '56 Marius Street Adelaide': 'Adelaide',
    '206 Old OK Building, Ratlou Location, Thabanchu 9781': 'Thaba Nchu',
    '57 Gemabok Avenues, 1st Floor Twin Cnr, Lenasia 1820 ': '57 Gemsbok Avenue, Lenasia',
    '56 Kruger Street, Forum Building, Bronkhorspruit, 1020': '56 Kruger Street, Bronkhorstspruit',
    'Office B59, Centurion Town Council, Cnr Rabie & Basen Rd, Liyleton, 0157': 'Cnr Rabie Road & Basen Road, Liyleton, 0157',
    '99 8th Avenue, Cnr Alfred Nzo Street, Alexandra Multipurpose Centre, Alexandra,': '99 8th Ave, Alexandra, 2014',
    '5th Floor Masa House, 12 New South Street, Gandhi Square, Mashalltown, 2001': '12 New South Street, Mashalltown, 2001',
    'Mini Munitoria Cnr Mgadi & Komane, Attridgeville,0008': 'Cnr Mgadi & Komane, Attridgeville, 0008',
    'Upper Floor 22 President Street, Focheville, 2515': '22 President Street, Fochville, 2515',
    '2nd Floor Office, No. 6, 28 Charmachael 2nd Floor Office, No. 6, 28 Charmachael': ' Carmichael Street, Ventersdorp, 2710 South Africa',
    'Shop No. 23 Corner De Kock Street, Sanlaam Centre, 8600': ' De Kock Street Vryburg 8600',
    '524 Main Road, Caltex Service Station, Senwabarwana, 0740': 'Blouberg Local Municipality, Limpopo',
    'Shop No 8 Nelson Mandela Street, City Square, Shop No 8 Nelson Mandela Street, City Square,': ' Nelson Mandela Street Lichtenburg 2740',
    'Shop 10 Roma Centre, Racing Park, Killaney, 7441': '-33.813884,18.534536',
    'Kaebetse Trading, 189 Groblersdall Road, Monsterlus,0470': '189 Groblersdall Road, Monsterlus, 0470',
    '463 Belvedere & Beatrix Street, Acadia, 0083': '463 Belvedere Street, Arcadia, Pretoria 0083',
    'DUMBERTON HOUSE 4TH FLOOR CHURCH STREET': '4th Floor Dumberton House,  Church Street, Cape town, 8001 South Africa',
    '771 Bombay Road, Truro Centre, Old Housing Offices, PMBurg, 3201': '771 Bombay Road, Pietermaritzburg 3201',
    '78 De Korte & De Beer Strts, Mineralia Bld, Braamfontein': '78 De Korte & De Beer Streets, Mineralia Bld, Braamfontein, 2000',
    '17 Arbee Drive, Office 1 MP Centre, Tongaat, 4068': 'Arbee Drive,Tongaat, 4068',
    'No. 23 Indian Shopping Complex, Salamat, No. 23 Indian Shopping Complex, Salamat,': 'Bloemhof, Lekwa-Teemane Local Municipality, North West 2662',
    '608,26 brown St Kakholo building': 'Brown St, Nelspruit, 1201 South Africa',
    'Office 6A, Bushbuckridge, Shopping Complex, 1280': 'Bushbuckridge, Shopping Complex, 1280',
    'Phesheya Kwenciba': 'Butterworth, 4960 South Africa',
    '12 Chestnut Crescent, A M Centre, Marianhill, 3610': 'Chestnut Crescent,  Marianhill, Durban 3610',
    'Office No 26, Civic Centre Building, Malamulele Main Road, 0950': 'Civic Centre Building, Malamulele Main Road, 0950',
    '138 Old Mutual Building, Unit F, Lebowakgomo, 0703': 'Cnr R518 and R517 Lebowakgomo, Limpopo ',
    'Cnr Voortrekker & Main Street, Sancam Building, 8460': 'Cnr Voortrekker & Main Street, Kuruman, 8460',
    'Community Hall Centre, Thembisa Section, Daantjie, 1200': 'Daantjie, 1200',
    'SB Farrow': 'East London, 5201 South Africa',
    'No. 1 Ebfin Centre, George Street, Athlone, 7766': 'George Street, Athlone, 7766',
    'Cnr Geriet & Marietz Streets, No 5 Old Cnr Geriet & Marietz Streets, No 5 Old': 'Gerrit Maritz St Zeerust 2865',
    'NY1, FAWO Building, Gugulethu, 7750': 'Gugulethu, 7750',
    '18 Vryburg Road, Molopo, Tosca, 8618': 'Tosca, North West, South Africa',
    '0ffice no 8,Khula Ntuli Building,Kwaggafontein,0458': 'Khula Ntuli Building Kwaggafontein,0458',
    'Lohatla': 'Postmasburg',
    'Shop no 22 GHL .Building Main Street Mkhuze 3965': 'Main Street Mkhuze 3965',
    'Engen Garage, Vleischboom, 1658': 'Makhuduthamaga Local Municipality',
    'Room 19 Balebogeng Centre, Tsoeu Street, Mamelodi West, 0122': 'Mamelodi West, Pretoria 0122',
    'Shop 4, Indian Centre, Amalia Road, Shop 4, Indian Centre, Amalia Road,': 'Mamusa Local Municipality Schweizer-Reneke 2780',
    'No.1 Mapela Stand, Metsotamia, Mapela, 0610': 'Mapela, Limpopo 0610',
    'Stand No.22294, Mohlalaotwane Village, Ga-Rakgodi, 1068': 'Marblehall, Limpopo',
    '1117 Farm 1, Superintendent Buildng, Mathabe Street, Mbibane, 0449': 'Mbibane, 0449',
    'OGS Building Centre, Room 141, Corner Street, 4th Avenue Town Centre, 7785': 'Mitchell\'s Plain, 7785',
    'Corner Gelead and Knobel Road, Ceres Moletjie, 0774': 'Moletji village, Limpopo 0774',
    'Stand No 4065, Mathibestad, 0404': 'Moretele ,Mathibestad Str,Hammanskraal 0404',
    'Shop No.2, Mphiwe Family Complex, 1360': 'Mphiwe Family Trust Complex Main Road, Acornhoek 1360',
    'D 254, Solomon Section, Main Road Mpuluzi, 2335': 'Mpuluzi, 2335, Mpumalanga South Africa',
    'Mabogo General Dealer, No 40, Ha Ravele, next to Ravele Bar Lounge and Nengovhela, Tshilwavhusiku,0920': 'Nengovhela Tshilwavhusiku, Limpopo 0920',
    'Stand 408 A, Ngwenyeni Main Road, KaMaqhekeza, 1346': 'Nkomazi, Mpumalanga, 1346',
    'PE Northern Areas': 'Salt Lake, Port Elizabeth',
    'Valoyi Traditional Authority Trust, Runnymead Trading Centre, Nwamitwa, 0871': 'Nwamitwa, 0871, Limpopo South Africa',
    'Ipelegeng Com. Centre, Cnr Phera & Khumalo White City Jabavu, 1868': 'Phera & Khumalo White City Jabavu, 1868',
    '597 Block H, Sekhing Village, near SASA Offices, 8566': 'Sekhing, Greater Taung Sekhing 8566',
    'Matsamo Lake Beneficiary Building,Shongwe Mission,1331': 'Shongwe Mission, 1331',
    'Shop No.1, Smiling Park, Mamotintane, next to the Stadium, Houtbos, Mankweng': 'Smiling Park Mankweng, Limpopo South Africa',
    'Oakley Trust, Stand 626, Mathibela Traditional Authority': 'Stand 620, Zone 1, Mankweng Polkwane 0727',
    'Pretelis Building, 6 Tambotie Street, Phalaborwa, 1398': 'Tambotie Street, Phalaborwa, 1398, Limpopo South Africa',
    '93 Lesedi Building, Main Road, Taung Station, 8580': 'Taung Station, North West 8580',
    'The Oaks Village Next to the Community Hall  , 1390': 'The Oaks Village Next to the Community Hall  , 1390',
    'Stand No 12 Far East, Tonga Road, Kwalugedlane, 1341': 'Tonga, Kwalugedlane, Komatipooort, 1341',
    'Sotobe Car Wash Premises, Tugela Ferry Main Rod opposite Msinga Municipality, Msinga, 3010': 'Tugela Ferry Rd, 3010',
    'Room 102 Union Rd Counsel Offices, Evaton, 2845': 'Union Rd, Evaton 2845',
    'No 09 Victoria Street, Build It Building, 2745': 'Victoria Rd Mahikeng 2745',
    '1375 The Village Mall, Stand No.1375, Elukwatini, 1192': 'village mall Elukwatini, 1192 City of Mpumalanga',
    'Shop No. 19, Kliptown Taxi Rank, Walter Sisulu Square, Kliptown, 1811': 'Walter Sisulu Square, Kliptown, Soweto 1811',
    '7450 Zwelitsha Street, Zone 1Diepkloof, 1864': 'Zone 1, Diepkloof, 1864 ',
    '11 Black Seed Centre, 2134 Zwane Street, Mbalentle, 2285': 'Zwane Street, Mbalentle, 2285',
    'No. 3 Setlagole Shopping Complex, Vryburg Road (N18), Setlagole Village, 2772': 'Vryburg Road, Ratlou, 2772',
    '53 Parakiet Street, Pescodia, Kimberly, 8309': '53 Parakiet Street, Kimberly, 8309',
    'Deep South': 'Fish Hoek',
    '45 main Street, Kirkwood, 6120': 'Kirkwood',
    '4 Thirteen Street Delaray, Roodepoort, 1724': 'No. 4 13th Street Delaray'
}


#from za-hansard
#https://github.com/mysociety/za-hansard/blob/6dbf92e43bd6e69d328162927a665a8dabf66307/za_hansard/question_scraper.py#L66
def check_output_wrapper(*args, **kwargs):

    # Python 2.7
    if hasattr(subprocess, 'check_output'):
        return subprocess.check_output(*args)

    # Backport to 2.6 from https://gist.github.com/edufelipe/1027906
    else:
        process = subprocess.Popen(stdout=subprocess.PIPE, *args, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get('args', args[0])
            error = subprocess.CalledProcessError(retcode, cmd)
            error.output = output
            raise error
        return output


def process_anc_province(text, province):
    source_urls = {
        'Eastern Cape': 'http://sourceafrica.net/documents/15394-anc-constituency-offices-eastern-cape-2014.html',
        'Free State': 'http://sourceafrica.net/documents/15395-anc-constituency-offices-free-state-2014.html',
        'Gauteng': 'http://sourceafrica.net/documents/15396-anc-constituency-offices-gauteng-2014.html',
        'Kwazulu Natal': 'http://sourceafrica.net/documents/15397-anc-constituency-offices-kwazulu-natal-2014.html',
        'Limpopo': 'http://sourceafrica.net/documents/15398-anc-constituency-offices-limpopo-2014.html',
        'Mpumalanga': 'http://sourceafrica.net/documents/15399-anc-constituency-offices-mpumalanga-2014.html',
        'North West': 'http://sourceafrica.net/documents/15400-anc-constituency-offices-north-west-2014.html',
        'Northern Cape': 'http://sourceafrica.net/documents/15401-anc-constituency-offices-northern-cape-2014.html',
        'Western Cape': 'http://sourceafrica.net/documents/15402-anc-constituency-offices-western-cape-2014.html'
    }
    source_url = source_urls[province]
    source_note = 'ANC %s Constituency List 2014' % (province)

    correct_title = {
        'ATLANTIS, MAMRE, PELLA,SURROUNDING FARMS': 'ATLANTIS, MAMRE, PELLA, SURROUNDING FARMS',
        'SENWABARWANA(BLOUBERG)': 'SENWABARWANA (BLOUBERG)'
    }

    offices = []

    title_pattern = " *([0-9]*)\.?\W*PCO CODE\W*([0-9]+) *([A-Za-z0-9,()/' ]+)"

    fields = [
        'MP',
        'Cell',
        'Administrator',
        'Physical Address',
        'Tel No',
        'Tel',
        'Fax No',
        'Fax',
        'E-mail',
        'Email',
        'Ward',
        'Municipality',
        'Region',
        'Postal Address',
        'Volunteer',
        'MPL',
        'Physical address',
        'Postal address',
        'Telefax',
        'Telfax',
        'Faxemail',
        'Wards',
        'Physical & Postal Address',
        'Tell',
        'ADSL',
        'Caucus Cell Phone'
    ]

    match_fields = ' *(?P<field>(' + ')|('.join(fields) + '))\W+(?P<value>.+)'

    correct_fields = {
        'Email': 'E-mail',
        'Telefax': 'Telfax',
        'Faxemail': 'Fax',
        'Wards': 'Ward',
        'Tell': 'Tel',
        'Tel No': 'Tel',
        'Fax No': 'Fax',
    }

    add_office = None
    previous_field = None
    set_next_cell = True

    for line in text.split("\n"):
        match_title = re.match(title_pattern, line)
        if match_title:
            #new office
            if add_office:
                if 'Physical Address' in add_office:
                    corrected = manual_location_corrections.get(
                        add_office['Physical Address'],
                        None)

                    if corrected:
                        add_office['Location'] = corrected

                offices.append(add_office)
                add_office = None

            title = match_title.group(3)
            title = title.replace('(to be relocated)', '')
            title = title.replace('(RELOCATED)', '')
            title = title.replace('(Office Is Relocating)', '')
            title = title.strip()
            title = correct_title.get(title, title)
            title = title.title()
            title = title.replace("'S", "'s")

            pco_code = match_title.group(2)

            add_office = {
                'Title': 'ANC Constituency Office (%s): %s' % (pco_code, title),
                'Province': province,
                'Type': 'office',
                'Source URL': source_url,
                'Source Note': source_note,
                'Party': 'ANC'
                }
            add_office['People'] = []
            if pco_code != '000':
                add_office['identifiers'] = {
                    'constituency-office/ANC/': pco_code
                }
        elif add_office:
            match_field = re.match(match_fields, line)
            if match_field:
                field = match_field.group('field').strip().title()
                value = match_field.group('value').strip()

                field = correct_fields.get(field, field)

                value = value.replace(u'Â', '')
                value = value.replace(u' ', ' ')
                value = value.replace(u'–', '-')
                value = value.replace(u'–', '-')

                prev = ['Physical Address', 'Postal Address', 'Ward']
                notin = ['Postal Address', 'Tel', 'Fax', 'E-mail', 'Ward', 'Municipality', 'Region']

                if field in ['Mp', 'Mpl']:
                    if 'Awaiting deployment' in value:
                        set_next_cell = False
                        continue
                    name = value

                    name = re.sub('-? ?(Deputy )?(Minister|NCOP)', '', name)
                    name = name.replace('Hon ', '')
                    name = name.replace('Dr ', '')
                    name = name.replace('Dep-Min. ', '')
                    name = name.replace('Min. ', '')
                    name = name.replace(' (Provincial)', '')
                    name = name.replace(' (NEC member)', '')

                    name = re.sub(
                        '-? ?\(? ?(Province to National) ?\)?',
                        '',
                        name
                    )
                    name = re.sub(
                        '–?-? NEC Deployee( &| and)?( Deputy)?( Minister)?',
                        '',
                        name
                    )
                    name = name.strip()
                    original_name = name
                    name = manual_name_corrections.get(name, name)

                    set_next_cell = True
                    person_to_append = {
                        'Name': name,
                        'Position': 'Constituency Contact'
                    }
                    if name != original_name:
                        person_to_append['Alternative Name'] = original_name
                    add_office['People'].append(person_to_append)

                elif field == 'Volunteer':
                    add_office['People'].append({
                        'Name': value.replace(',', ''),
                        'Position': 'Volunteer'
                    })

                elif field == 'Administrator':
                    name = value
                    name = manual_name_corrections.get(name, name)
                    name = name.replace(',', '').replace('/', '').strip()
                    position = 'Administrator'

                    #ignore vacancies
                    if 'Vacant' in name:
                        set_next_cell = False
                        continue

                    #correctly label volunteer administrators
                    if '(Volunteer)' in value:
                        name = name.replace('(Volunteer)', '').strip()
                        position = 'Administrator (volunteer)'

                    set_next_cell = True
                    add_office['People'].append({
                        'Name': name,
                        'Position': position
                    })

                elif field == 'Cell':
                    #cell is only recorded with the previous person
                    if len(add_office['People']) > 0 and set_next_cell:
                        #remove odd unicode characters in cell numbers
                        value = re.sub('\W', ' ', value)
                        person_index = len(add_office['People'])-1
                        add_office['People'][person_index][field] = value

                elif field == 'Physical & Postal Address':
                    #split combined field into two
                    add_office['Postal Address'] = value
                    add_office['Physical Address'] = value

                elif field == 'Telfax':
                    #split combined field into two
                    add_office['Tel'] = value
                    add_office['Fax'] = value

                else:
                    #field for the office/area
                    add_office[field] = value

                previous_field = field

            #handle combined fields that span more than one line
            elif previous_field == 'Physical & Postal Address':
                add_office['Postal Address'] = add_office['Postal Address'] + ' ' + value
                add_office['Physical Address'] = add_office['Physical Address'] + ' ' +value

            #handle fields that span more than one line
            elif previous_field in prev and not line.strip() in notin:
                add_office[previous_field] = add_office[previous_field] + ' ' + line.strip()

            elif line.strip() != '':
                print 'Unmatched line:', line

    if 'Physical Address' in add_office:
        corrected = manual_location_corrections.get(add_office['Physical Address'], None)

        if corrected:
            add_office['Location'] = corrected

    offices.append(add_office)
    return offices


def process_da_areas(csv_file):
    areas = {}

    source_url = 'http://sourceafrica.net/documents/15403-da-constituency-areas-2014.html'
    source_note = 'DA Constituency List 2014'

    with open(csv_file, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                continue

            if row[2].strip() in areas:
                #area already exists - just add the person
                original_name = row[1]
                name = manual_name_corrections.get(row[1], row[1])

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'}

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                areas[row[2].strip()]['People'].append(person_to_append)

            else:
                #add new area
                original_name = row[1]
                name = manual_name_corrections.get(row[1], row[1])

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'}

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                areas[row[2].strip()] = {
                    'Title': row[2].strip(),
                    'People': [
                        person_to_append
                    ],
                    'Description': row[5],
                    'Province': row[4],
                    'Type': 'area',
                    'Source URL': source_url,
                    'Source Note': source_note,
                    'Party': 'DA'
                }
                if row[3] != '':
                    areas[row[2].strip()]['Location'] = manual_location_corrections.get(row[3], row[3])

    offices = []
    for area_name, area in areas.items():
        offices.append(area)

    return offices


def process_eff_offices(csv_file):
    offices_to_add = {}

    source_url = 'http://sourceafrica.net/documents/15405-eff-constituency-offices-2014.html'
    source_note = 'EFF Constituency List 2014'

    with open(csv_file, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                continue

            if row[0].strip() in offices_to_add:
                #office exists - just add person
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                offices_to_add[row[0].strip()]['People'].append(person_to_append)

            else:
                #add new office
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                offices_to_add[row[0].strip()] = {
                    'Title': row[0].strip(),
                    'People': [
                        person_to_append
                    ],
                    'Tel': row[5],
                    'Province': row[2].title(),
                    'Physical Address': manual_location_corrections.get(row[3], row[3]).title(),
                    'Type': 'office',
                    'Source URL': source_url,
                    'Source Note': source_note,
                    'Party': 'EFF'
                }

                if row[4] != '':
                    administrator_to_append = {
                        'Name': row[4].title(),
                        'Position': 'Administrator'
                    }
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

    offices = []
    for office_name, office in offices_to_add.items():
        offices.append(office)

    return offices


def process_aic_offices(csv_file):
    offices_to_add = {}

    source_url_1 = 'http://sourceafrica.net/documents/15404-aic-constituencies-offices-2014.html'
    source_note_1 = 'AIC Constituency List 2014'
    source_url_2 = 'http://sourceafrica.net/documents/15406-pmg-sourced-constituency-office-data.html'
    source_note_2 = 'Constituency data collected by PMG 2014'

    with open(csv_file, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                continue

            if row[0].strip() in offices_to_add:
                #office exists - just add person
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()]['People'].append(person_to_append)

            else:
                #add new office
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()] = {
                    'Title': row[0].strip(),
                    'People': [],
                    'Tel': row[6],
                    'Fax': row[7],
                    'Province': row[5],
                    'Physical Address': manual_location_corrections.get(row[4], row[4]),
                    'Type': 'office',
                    'Sources': [
                        {
                            'Source URL': source_url_1,
                            'Source Note': source_note_1
                        },
                        {
                            'Source URL': source_url_2,
                            'Source Note': source_note_2
                        },
                    ],
                    'Party': 'AIC'
                }

                if name != '':
                    offices_to_add[row[0].strip()]['People'].append(person_to_append)

                if row[8] != '':
                    administrator_to_append = {
                        'Name': row[8],
                        'Position': 'Administrator'
                    }
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

                if row[9] != '':
                    administrator_to_append = {
                        'Name': row[9],
                        'Position': 'Coordinator'
                    }
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

                if row[10] != '':
                    administrator_to_append = {
                        'Name': row[10],
                        'Position': 'Community Development Field Worker'
                    }
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

    offices = []
    for office_name, office in offices_to_add.items():
        offices.append(office)

    return offices

def process_acdp_offices(csv_file):
    offices_to_add = {}

    source_url = 'http://sourceafrica.net/documents/15406-pmg-sourced-constituency-office-data.html'
    source_note = 'Constituency data collected by PMG 2014'

    with open(csv_file, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                continue

            if row[0].strip() in offices_to_add:
                #office exists - just add person
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()]['People'].append(person_to_append)

            else:
                #add new office
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()] = {
                    'Title': row[0].strip(),
                    'People': [],
                    'Tel': row[6],
                    'Fax': row[7],
                    'Province': row[5],
                    'Physical Address': manual_location_corrections.get(row[4], row[4]),
                    'Type': 'office',
                    'Source URL': source_url,
                    'Source Note': source_note,
                    'Party': 'ACDP'
                }

                if name != '':
                    offices_to_add[row[0].strip()]['People'].append(person_to_append)

                if row[8] != '':
                    administrator_to_append = {
                        'Name': row[8],
                        'Position': 'Administrator'
                    }
                    if row[9] != '':
                        administrator_to_append['Cell'] = row[9]
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

    offices = []
    for office_name, office in offices_to_add.items():
        offices.append(office)

    return offices

def process_ff_offices(csv_file):
    offices_to_add = {}

    source_url = 'http://sourceafrica.net/documents/15406-pmg-sourced-constituency-office-data.html'
    source_note = 'Constituency data collected by PMG 2014'

    with open(csv_file, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                continue

            if row[0].strip() in offices_to_add:
                #office exists - just add person
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()]['People'].append(person_to_append)

            else:
                #add new office
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()] = {
                    'Title': row[0].strip(),
                    'People': [],
                    'Tel': row[6],
                    'Fax': row[7],
                    'Province': row[5],
                    'Physical Address': manual_location_corrections.get(row[4], row[4]),
                    'Type': 'office',
                    'Source URL': source_url,
                    'Source Note': source_note,
                    'Party': 'FF'
                }

                if name != '':
                    offices_to_add[row[0].strip()]['People'].append(person_to_append)

                if row[8] != '':
                    administrator_to_append = {
                        'Name': row[8],
                        'Position': 'Administrator'
                    }
                    if row[9] != '':
                        administrator_to_append['Cell'] = row[9]
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

    offices = []
    for office_name, office in offices_to_add.items():
        offices.append(office)

    return offices

def process_apc_offices(csv_file):
    offices_to_add = {}

    source_url = 'http://sourceafrica.net/documents/15406-pmg-sourced-constituency-office-data.html'
    source_note = 'Constituency data collected by PMG 2014'

    with open(csv_file, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                continue

            if row[0].strip() in offices_to_add:
                #office exists - just add person
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()]['People'].append(person_to_append)

            else:
                #add new office
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()] = {
                    'Title': row[0].strip(),
                    'People': [],
                    'Tel': row[6],
                    'Fax': row[7],
                    'Province': row[5],
                    'Physical Address': manual_location_corrections.get(row[4], row[4]),
                    'Type': 'office',
                    'Source URL': source_url,
                    'Source Note': source_note,
                    'Party': 'APC'
                }

                if name != '':
                    offices_to_add[row[0].strip()]['People'].append(person_to_append)

                if row[8] != '':
                    administrator_to_append = {
                        'Name': row[8],
                        'Position': 'Administrator'
                    }
                    if row[9] != '':
                        administrator_to_append['Cell'] = row[9]
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

    offices = []
    for office_name, office in offices_to_add.items():
        offices.append(office)

    return offices

def process_udm_offices(csv_file):
    offices_to_add = {}

    source_url = 'http://sourceafrica.net/documents/15406-pmg-sourced-constituency-office-data.html'
    source_note = 'Constituency data collected by PMG 2014'

    with open(csv_file, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                continue

            if row[0].strip() in offices_to_add:
                #office exists - just add person
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()]['People'].append(person_to_append)

            else:
                #add new office
                name = re.sub('Mr?s?.? ', '', row[1].strip().title())
                name = re.sub('\ADr.? ', '', name).strip()
                original_name = name
                name = manual_name_corrections.get(name, name)

                person_to_append = {
                    'Name': name,
                    'Position': 'Constituency Contact'
                }

                if name != original_name:
                    person_to_append['Alternative Name'] = original_name

                if row[2] != '':
                    person_to_append['Cell'] = row[2]

                if row[3] != '':
                    person_to_append['Email'] = row[3]

                offices_to_add[row[0].strip()] = {
                    'Title': row[0].strip(),
                    'People': [],
                    'Tel': row[6],
                    'Fax': row[7],
                    'Province': row[5],
                    'Physical Address': manual_location_corrections.get(row[4], row[4]),
                    'Type': 'office',
                    'Source URL': source_url,
                    'Source Note': source_note,
                    'Party': 'UDM'
                }

                if name != '':
                    offices_to_add[row[0].strip()]['People'].append(person_to_append)

                if row[8] != '':
                    administrator_to_append = {
                        'Name': row[8],
                        'Position': 'Administrator'
                    }
                    if row[9] != '':
                        administrator_to_append['Cell'] = row[9]
                    offices_to_add[row[0].strip()]['People'].append(administrator_to_append)

    offices = []
    for office_name, office in offices_to_add.items():
        offices.append(office)

    return offices

ensure_executable_found("antiword")

provinces = [
    'Eastern Cape',
    'Free State',
    'Gauteng',
    'Kwazulu Natal',
    'Limpopo',
    'Mpumalanga',
    'North West',
    'Northern Cape',
    'Western Cape'
]

offices = []

for province in provinces:
    text = check_output_wrapper(['antiword', '2014/ANC/'+province+'.doc']).decode('unicode-escape')
    offices = offices + process_anc_province(text, province)

offices = offices + process_da_areas('2014/DA_processed.csv')

offices = offices + process_eff_offices('2014/EFF_processed.csv')

offices = offices + process_aic_offices('2014/AIC_processed.csv')

offices = offices + process_acdp_offices('2014/ACDP_processed.csv')

offices = offices + process_ff_offices('2014/FFplus_processed.csv')

offices = offices + process_apc_offices('2014/APC_processed.csv')

offices = offices + process_udm_offices('2014/UDM_processed.csv')

exclude = [
    'COPE'
]

json_output = {
    'offices': offices,
    'exclude': exclude,
    'start_date': '2014-05-21',
    'end_date': '2014-05-06'}

with open('2014.json', 'w') as output:
    json.dump(json_output, output, indent=4)

