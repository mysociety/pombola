#!/usr/bin/env python

# Take the json in the file given as first argument and convert it to the JSON
# format needed for import. Should do all cleanup of data and removal of
# unneeded entries too.

import sys
import os
import json
import re
import urllib

script_dir = os.path.basename(__file__)
base_dir = os.path.join(script_dir, "../../../../..")
app_path = os.path.abspath(base_dir)
sys.path.append(app_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'pombola.settings.south_africa'

from django.utils.text import slugify
from django.db.models import Q

from pombola.core.models import Person

class Converter(object):

    groupings = []

    ditto_marks = [
        "\"",
        "\" \"",
    ]

    # Change this to True to enable little bits of helper code for finding new
    # slug corrections:
    finding_slug_corrections = False

    slug_corrections = {
        "albert-theo-fritz": "albert-fritz",
        "albertinah-nomathuli-luthuli": "a-n-luthuli",
        "amos-matila": "amos-gerald-matila",
        "andre-gaum": "andre-hurtley-gaum",
        "andrew-louw": "a-louw",
        "anele-mda": "a-mda",
        "anton-alberts": "anton-de-waal-alberts",
        "archibold-mzuvukile-figlan": "a-m-figlan",
        "archibold-nyambi": "archibold-jomo-nyambi",
        "arthur-ainslie": "arthur-roy-ainslie",
        "bafunani-aaron-mnguni": "bafumani-aaron-mnguni",
        "barbara-anne-hogan": "b-a-hogan",
        "barbara-thompson": "barbara-thomson",
        "bertha-mabe": "bertha-peace-mabe",
        "beryl-ferguson": "beryl-delores-ferguson",
        "beverley-lynnette-abrahams": "beverley-lynette-abrahams",
        "bhekizizwe-abram-radebe": "bhekiziswe-abram-radebe",
        "bonginkosi-dhlamini": "bonginkosi-dlamini",
        "bonisile-alfred-nesi": "bonisile-nesi",
        "busisiwe-mncube": "busisiwe-veronica-mncube",
        "butana-moses-komphela": "b-m-komphela",
        "buyelwa-patience-sonjica": "b-p-sonjica",
        "buyiswa-diemu": "buyiswa-cornelia-diemu",
        "buyiswa-diemublaai": "buyiswa-cornelia-diemu",
        "cassel-mathale": "cassel-charlie-mathale",
        "charel-de-beer": "charel-jacobus-de-beer",
        "constance-mosimane": "constance-kedibone-kelekegile-mosimane",
        "cq-madlopha": "celiwe-qhamkile-madlopha",
        "crosby-mpozo-moni": "crosby-mpoxo-moni",
        "dalitha-boshigo": "dalitha-fiki-boshigo",
        "danny-montsitsi": "sediane-danny-montsitsi",
        "dennis-bloem": "dennis-victor-bloem",
        "dennis-gamede": "dumisani-dennis-gamede",
        "desiree-van-der-walt": "d-van-der-walt",
        "dina-deliwa-pule": "dina-deliwe-pule",
        "dirk-feldman": "dirk-benjamin-feldman",
        "dj-stubbe": "dirk-jan-stubbe",
        "doris-nompendlko-ngcengwane": "nompendlko-doris-ngcengwane",
        "dudu-chili": "dudu-olive-chili",
        "duduzile-sibiya": "dudu-sibiya",
        "dumisani-ximbi": "dumsani-livingstone-ximbi",
        "ebrahim-ebrahim": "ebrahim-ismail-ebrahim",
        "elza-van-lingen": "elizabeth-christina-van-lingen",
        "emmanuel-nkosinathi-mandlenkosi-mthethwa": "emmanuel-nkosinathi-mthethwa",
        "enoch-godongwana": "e-godongwana",
        "ernst-eloff": "ernst-hendrik-eloff",
        "faith-bikani": "faith-claudine-bikani",
        "gbd-mcintosh": "graham-brian-douglas-mc-intosh",
        "gelana-sindane": "gelana-sarian-sindane",
        "geoffery-quinton-mitchell-doidge": "g-q-m-doidge",
        "geolatlhe-godfrey-oliphant": "gaolatlhe-godfrey-oliphant",
        "geordin-hill-lewis": "geordin-gwyn-hill-lewis",
        "george-boinamo": "george-gaolatlhe-boinamo",
        "gloria-borman": "gloria-mary-borman",
        "graham-peter-dalziel-mackenzie": "graham-peter-dalziel-mac-kenzie",
        "gratitude-bulelani-magwanishe": "gratitude-magwanishe",
        "gregory-krumbock": "gregory-rudy-krumbock",
        "gwedoline-lindiwe-mahlangu-nkabinde": "g-l-mahlangu-nkabinde",
        "helen-line": "helen-line-hendriks",
        "hendrietta-bogopane-zulu": "hendrietta-ipeleng-bogopane-zulu",
        "herman-groenewald": "hermanus-bernadus-groenewald",
        "hildah-sizakele-msweli": "hilda-sizakele-msweli",
        "isaac-mfundisi": "isaac-sipho-mfundisi",
        "ismail-vadi": "i-vadi",
        "jac-bekker": "jacobus-marthinus-g-bekker",
        "james-lorimer": "james-robert-bourne-lorimer",
        "jan-gunda": "jan-johannes-gunda",
        "jf-smalle": "jacobus-frederik-smalle",
        "johanna-fredrika-terblanche": "johanna-fredrika-juanita-terblanche",
        "john-moepeng": "john-kabelo-moepeng",
        "joseph-job-mc-gluwa": "joseph-job-mcgluwa",
        "keith-muntuwenkosi-zondi": "k-m-zondi",
        "kenneth-raselabe-meshoe": "kenneth-raselabe-joseph-meshoe",
        "kennett-andrew-sinclair": "kenneth-andrew-sinclair",
        "lekaba-jack-tolo": "l-j-tolo",
        "lemias-buoang-mashile": "buoang-lemias-mashile",
        "leonard-ramatlakana": "leonard-ramatlakane",
        "liezl-van-der-merwe": "liezl-linda-van-der-merwe",
        "lulama-mary-theresa-xingwana": "lulama-marytheresa-xingwana",
        "lusizo-makhubela-mashele": "lusizo-sharon-makhubela-mashele",
        "lydia-sindiswe-chikunga": "lydia-sindisiwe-chikunga",
        "machejane-alina-rantsolase": "m-a-rantsolase",
        "mafemane-makhubela": "mafemane-wilson-makhubela",
        "maite-emely-nkoana-mashabane": "maite-emily-nkoana-mashabane",
        "makgathatso-pilane-majake": "makgathatso-charlotte-chana-pilane-majake",
        "makhenkezi-arnold-stofile": "m-a-stofile",
        "makone-collen-maine": "mokoane-collen-maine",
        "mandlenkosi-enock-mbili": "m-e-mbili",
        "mark-harvey-steele": "m-h-steele",
        "mary-anne-lindelwa-dunjwa": "mary-ann-lindelwa-dunjwa",
        "masefako-dikgale": "masefako-clarah-digkale",
        "matome-mokgobi": "matome-humphrey-mokgobi",
        "mavis-nontsikelelo-magazi": "n-m-magazi",
        "mavis-ntebaleng-matladi": "m-n-matladi",
        "max-vuyisile-sisuslu": "max-vuyisile-sisulu",
        "mbhazima-samuel-shilowa": "m-s-shilowa",
        "mbuyiselo-jacobs": "mbuyiselo-patrick-jacobs",
        "membathisi-mphumzi-shepherd-mdladlana": "m-m-s-mdladlana",
        "meriam-phaliso": "meriam-nozibonelo-phaliso",
        "michael-de-villiers": "michael-jacobs-roland-de-villiers",
        "michael-james-ellis": "m-j-ellis",
        "mmatlala-boroto": "mmatlala-grace-boroto",
        "mninwa-mahlangu": "mninwa-johannes-mahlangu",
        "mntombizodwa-florence-nyanda": "n-f-nyanda",
        "mogi-lydia-moshodi": "moji-lydia-moshodi",
        "mohammed-sayedali-shah": "mohammed-rafeek-sayedali-shah",
        "mondli-gungubele": "m-gungubele",
        "mosie-anthony-cele": "mosie-antony-cele",
        "mpane-mohorosi": "mpane-martha-mohorosi",
        "n-d-ntwanambi": "nosipho-dorothy-ntwanambi",
        "nolitha-yvonne-vukuza-linda": "n-y-vukuza-linda",
        "noluthando-agatha-mayende-sibiya": "n-a-mayende-sibiya",
        "nomzamo-winnie-madikizela-mandela": "nomzamo-winfred-madikizela-mandela",
        "nonkumbi-bertha-gxowa": "n-b-gxowa",
        "ntombikhayise-nomawisile-sibhida": "ntombikayise-nomawisile-sibhida",
        "ntombikhayise-nomawisile-sibhidla": "ntombikayise-nomawisile-sibhida",
        "obed-bapela": "kopeng-obed-bapela",
        "onel-de-beer": "onell-de-beer",
        "pakishe-motsoaledi": "pakishe-aaron-motsoaledi",
        "patrick-chauke": "h-p-chauke",
        "paul-mashatile": "shipokasa-paulus-mashatile",
        "pearl-petersen-maduna": "pearl-maduna",
        "petronella-catharine-duncan": "petronella-catherine-duncan",
        "petrus-johannes-christiaan-pretorius": "p-j-c-pretorius",
        "phillip-david-dexter": "p-d-dexter",
        "rachel-rasmeni": "rachel-nomonde-rasmeni",
        "radhakrishna-lutchmana-padayachie": "r-l-padayachie",
        "raseriti-tau": "raseriti-johannes-tau",
        "rebecca-m-motsepe": "rebecca-mmakosha-motsepe",
        "refilwe-junior-mashigo": "refilwe-modikanalo-mashigo",
        "regina-lesoma": "regina-mina-mpontseng-lesoma",
        "rejoice-thizwilondi-mabudafhasi": "thizwilondi-rejoyce-mabudafhasi",
        "richard-baloyi": "masenyani-richard-baloyi",
        "robert-lees": "robert-alfred-lees",
        "roland-athol-trollip": "roland-athol-price-trollip",
        "royith-bhoola": "royith-baloo-bhoola",
        "salamuddi-abram": "salamuddi-salam-abram",
        "sam-mazosiwe": "siphiwo-sam-mazosiwe",
        "sanna-keikantseeng-molao-now-plaatjie": "sanna-keikantseeng-plaatjie",
        "sanna-plaatjie": "sanna-keikantseeng-plaatjie",
        "seeng-patricia-lebenya-ntanzi": "s-p-lebenya-ntanzi",
        "sherphed-mayatula": "shepherd-malusi-mayatula",
        "sherry-chen": "sheery-su-huei-cheng",
        "sicelo-shiceka": "s-shiceka",
        "siyabonga-cwele": "siyabonga-cyprian-cwele",
        "stella-tembisa-ndabeni-abrahams": "stella-tembisa-ndabeni",
        "suhla-james-masango": "s-j-masango",
        "swaphi-h-plaatjie": "swaphi-hendrick-plaatjie",
        "swaphi-plaatjie": "swaphi-hendrick-plaatjie",
        "teboho-chaane": "teboho-edwin-chaane",
        "thabo-makunyane": "thabo-lucas-makunyane",
        "thandi-vivian-tobias-pokolo": "thandi-vivian-tobias",
        "thembalani-waltemade-nxesi": "thembelani-waltermade-nxesi",
        "tim-harris": "timothy-duncan-harris",
        "tjheta-mofokeng": "tjheta-makwa-harry-mofokeng",
        "tlp-nwamitwa-shilubana": "tinyiko-lwandlamuni-phillia-nwamitwa-shilubana",
        "tovhowani-josephine-tshivhase": "t-j-tshivhase",
        "trevor-john-bonhomme": "trevor-bonhomme",
        "tshenuwani-simon-farisani": "t-s-farisani",
        "tshiwela-elidah-lishivha": "tshiwela-elida-lishivha",
        "velly-manzini": "velly-makasana-manzini",
        "willem-faber": "willem-frederik-faber",
        "willem-phillips-doman": "w-p-doman",
        "zephroma-dubazana": "zephroma-sizani-dubazana",
        "zephroma-sizani-dlamini-dubazana": "zephroma-sizani-dubazana",
        "zisiwe-balindlela": "zisiwe-beauty-nosimo-balindlela",
        "zoliswa-kota-fredericks": "zoliswa-albertina-kota-fredericks",
        "zukiswa-rantho": "daphne-zukiswa-rantho",
        "seiso-mohai": "seiso-joel-mohai",
        "belinda-bozzoli-van-onsellen": "belinda-bozzoli",
        "micheal-cardo": "michael-john-cardo",
        "zephroma-dlamini-dubazana": "zephroma-sizani-dubazana",
        "pravin-jamnadas-gordhan": "pravin-gordhan",
        "barnard-joseph": "bernard-daniel-joseph",
        "diane-kohler": "dianne-kohler-barnard",
        "dean-macpherson": "dean-william-macpherson",
        "thembekile-majola": "richard-majola",
        "edwin-makue": "eddie-makue",
        "mmoba-malatsi-seshoka": "mmoba-solomon-seshoka",
        "suhla-masango": "bridget-staff-masango",
        "lindiwe-maseko": "maseko-lindiwe",
        "shipokosa-mashatile": "shipokasa-paulus-mashatile",
        "comely-maxegwana": "humphrey-maxegwana",
        "lungi-mnganga-gcabashe": "lungi-annette-mnganga-gcabashe",
        "pumzile-mnguni": "phumzile-justice-mnguni",
        "mohapi-mohapi": "mohapi-jihad-mohapi",
        "charles-nqakula": "c-nqakula",
        "bhekiziwe-radebe": "bhekiziswe-abram-radebe",
        "david-ross": "david-christie-ross",
        "olifile-sefako": "olefile-sefako",
        "sheila-shope-sithole": "sheila-coleen-nkhensani-sithole",
        "christiaan-smit": "christiaan-frederik-beyers-smit",
        "makhotso-magdaline-sotyu": "makhotso-magdeline-sotyu",
        "johnna-terblanche": "johanna-fredrika-juanita-terblanche",
        "thandi-tobias-pokolo": "thandi-vivian-tobias",
        "tshoganetso-tongwane-gasebonwe": "tshoganetso-mpho-adolphina-tongwane",
        "shiella-xego-sovita": "sheilla-tembalam-xego-sovita",
        "winile-zondi": "wp-zondi",
        "lindiwe-zulu": "l-d-zulu",
        "lungelwa-zwane": "ll-zwane",
        "mamonare-chueu": "chueu-patricia",
        "stanford-gana": "makashule-gana",
        "hendrik-kruger": "hendrik-christiaan-crafford-kruger",
        "dipuo-letsatsi-duba": "ms-letsatsi-duba-db",
        "nomaindiya-mfeketo": "nomaindiya-cathleen-mfeketho",
        "claudia-ndaba": "ndaba-nonhlanhla",
        "maureen-scheepers": "m-scheepers",
        "nomaindiya-cathleen-mfeketo": "nomaindiya-cathleen-mfeketho",
        "tshoganetso-mpho-adolphina-gasebonwe": "tshoganetso-mpho-adolphina-gasebonwe-tongwane",
        "mntomuhle-khawula": "m-khawula",
        "thembekile-richard-majola": "richard-majola",
        "natasha-mazzone": "natasha-wendy-anita-michael",
        "zukiswa-ncitha": "zukiswa-veronica-ncitha",
        "cathlene-labuschagne": "cathleen-labuschagne",
        "tandi-gloria-mpambo-sibhukwana": "thandi-gloria-mpambo-sibhukwana",
        "tandi-mpambo-sibhukwana": "thandi-gloria-mpambo-sibhukwana",
        "marshall-mzingisi-dlamini": "mzingisi-marshall-dlamini",
        "hlengiwe-octavia-maxon": "hlengiwe-octavia-hlophe",
        "hlengiwe-maxon": "hlengiwe-octavia-hlophe",
        "norbet-buthelezi": "sfiso-norbert-buthelezi",
        "christian-hattingh": "chris-hattingh",
        "karen-jooste-de-kock": "karen-de-kock",
        "ntombovuyo-mente-nqweniso": "ntombovuyo-veronica-nqweniso",
        "ockers-stefanus-terblanche": "ockert-stefanus-terblanche",
        "patrick-maloyi": "nono-maloyi",
        "ghaleb-cachalia": "ghaleb-cachalia",
        "archibold-figlan": "a-m-figlan",
        "hlengiwe-hlophe-maxon": "hlengiwe-octavia-hlophe",
        "nkagisang-koni-mokgosi": "nkagisang-poppy-mokgosi",
        "terrence-mpanza": "terence-skhumbuzo-mpanza",
        "phoebe-abraham-ntantiso": "noxolo-abraham-ntantiso",
        "hlengiwe-o-hlophe-mkhaliphi": "hlengiwe-octavia-hlophe",
        "mohammed-hoosen": "mohammed-haniff-hoosen",
        "rainey-hugo": "reiney-thamie-hugo",
        "gwede-samson-mantashe": "gwede-mantashe",
        "moses-masango": "moses-siphosezwe-amos-masango",
        "joseph-mc-gluwa": "joseph-job-mcgluwa",
        "lehlohonolo-mokoena": "lehlohonolo-goodwill-mokoena",
        "busisiwe-ndlovu": "busisiwe-clarah-ndlovu",
        "gwen-ngwenya": "amanda-ngwenya",
        "neliswa-nkonyeni": "np-nkonyeni",
        "hendrik-schmidt": "hendrik-cornelius-schmidt",
        "zolile-xalisa": "zolile-roger-xalisa",
        "thandiwe-alina-mfulo": "alina-mfulo",
        "micheal-shackleton": "michael-stephen-shackleton",
        #name changes confirmed in National Assembly membership document
        "buyiswa-blaai": "buyiswa-cornelia-diemu",
        "sanna-keikantseeng-molao": "sanna-keikantseeng-plaatjie",
        # Garbage entries
        "control-flag-ict": None,
    }

    category_sort_orders = {
        "SHARES AND OTHER FINANCIAL INTERESTS": 1,
        "REMUNERATED EMPLOYMENT OUTSIDE PARLIAMENT": 2,
        "DIRECTORSHIP AND PARTNERSHIPS": 3,
        "CONSULTANCIES OR RETAINERSHIPS": 4,
        "SPONSORSHIPS": 5,
        "GIFTS AND HOSPITALITY": 6,
        "BENEFITS": 7,
        "TRAVEL": 8,
        "LAND AND PROPERTY": 9,
        "PENSIONS": 10,
        "CONTRACTS": 11,
        "TRUSTS": 12,
        "ENCUMBERANCES": 13,
    }

    def __init__(self, filename):
        self.filename = filename

    def convert(self):
        data = self.extract_data_from_json()

        self.extract_release(data)
        self.extract_entries(data)

        return self.produce_json()

    def extract_release(self, data):
        source_url = data['source']
        year = data['year']
        date = data['date']

        source_filename = re.sub(r'.*/(.*?)\.pdf', r'\1', source_url)
        source_name = urllib.unquote(source_filename).replace('_', ' ').strip()

        self.release = {
            "name": "Parliament Register of Members' Interests " + year,
            "date": date,
            "source_url": source_url,
        }

    def extract_entries(self, data):
        for register_entry in data['register']:
            for raw_category_name, entries in register_entry.items():
                # we only care about entries that are arrays
                if type(entries) != list:
                    continue

                # go through all entries stripping off extra whitespace from
                # keys and values
                for entry in entries:
                    for key in entry.keys():

                        # correct common scraper heading error
                        key_to_use = key.strip()
                        if key_to_use == 'Benefits' and raw_category_name.strip() == "TRUSTS":
                            key_to_use = "Details Of Benefits"

                        entry[key_to_use] = entry.pop(key).strip()

                    if entry.get('No') == 'Nothing to disclose':
                        del entry['No']

                # Need to be smart about values that are just '"' as these are dittos of the previous entries.
                previous_entries = []
                for entry in entries:
                    if len(previous_entries):
                        for key in entry.keys():
                            if entry[key] in self.ditto_marks:
                                for previous in reversed(previous_entries):
                                    if key in previous:
                                        entry[key] = previous[key]
                                        break
                                # Replacement may not have been found, warn
                                # if entry[key] in self.ditto_marks:
                                #     sys.stderr.write("----------- Could not find previous entry for ditto mark of '{0}'\n".format(key))
                                #     sys.stderr.write(str(previous_entries) + "\n")
                                #     sys.stderr.write(str(entry) + "\n")
                    previous_entries.append(entry)

                # Filter out entries that are empty
                entries = [ e for e in entries if len(e) ]

                if len(entries) == 0:
                    continue

                grouping = {
                    "release": self.release,
                    "entries": entries,
                }

                # Extract the category name we are interested in
                category_name = raw_category_name.strip()
                category_name = re.sub(r'^\d+\.\s*', '', category_name)

                grouping['category'] = {
                    "sort_order": self.category_sort_orders[category_name],
                    "name": category_name,
                }

                # Work out who the person is
                person_slug = self.mp_to_person_slug(register_entry['mp'])
                if not person_slug:
                    continue # skip if no slug
                grouping['person'] = {
                    "slug": person_slug
                }


                self.groupings.append(grouping)

            # break # just for during dev

    def mp_to_person_slug(self, mp):
        muddled_name, party = re.search(r'^(.*)\s\(+(.*?)\)+', mp).groups()
        name = re.sub(r'(.*?), (.*)', r'\2 \1', muddled_name)
        slug = slugify(name)

        # Check if there is a known correction for this slug
        slug = self.slug_corrections.get(slug, slug)

        # Sometimes we know we can't resolve the person
        if slug is None:
            return None

        try:
            person = Person.objects.get(slug=slug)
            return person.slug
        except Person.DoesNotExist:
            try:
                name_parts = re.findall(r'(.*?), (.*)', muddled_name)
                person = Person.objects.get(Q(slug__contains=slugify(name_parts[0][0])) & Q(slug__contains=slugify(name_parts[0][1])))
                return person.slug
            except Person.DoesNotExist:
                last_name = name.split(' ')[-1]

                possible_persons = Person.objects.filter(legal_name__icontains=last_name)

                if self.finding_slug_corrections and possible_persons.count() == 1:
                    possible_slug = possible_persons.all()[0].slug
                    self.slug_corrections[slug] = possible_slug
                    return possible_slug

                for person in possible_persons:
                    print 'perhaps: "{0}": "{1}",'.format(slug, person.slug)
                else:
                    print "no possible matches for {0}".format(slug)

                raise Exception("Slug {0} not found, please find matching slug and add it to the slug_corrections".format(slug))

    def produce_json(self):
        data = self.groupings

        combined_data = self.combine_data(data)

        out = json.dumps(combined_data, indent=4, sort_keys=True)
        return re.sub(r' *$', '', out, flags=re.M)

    def combine_data(self, data):
        """
        Manipulate the data so that there are no duplicates of person and
        category, and sort data so that it is diff-able.
        """
        sorted_data = sorted(
            data,
            key = lambda x: x['person']['slug'] + ':' + x['category']['name']
        )

        combined_data = []

        for entry in sorted_data:
            # check if the last entry of combined_data has same person and
            # category. If so add entries to that, otherwise append whole thing.

            if len(combined_data):
                last_entry = combined_data[-1]
            else:
                last_entry = None

            if last_entry and last_entry['person']['slug'] == entry['person']['slug'] and last_entry['category']['name'] == entry['category']['name']:
                last_entry['entries'].extend(entry['entries'])
            else:
                combined_data.append(entry)

        return combined_data


    def extract_data_from_json(self):
        with open(self.filename) as fh:
            return json.load(fh)


if __name__ == "__main__":
    converter = Converter(sys.argv[1])
    output = converter.convert()
    print output

    if converter.finding_slug_corrections:
        print "\n\n"
        print "#### COPY THIS TO slug_corrections and s/null/None/ :) ####"
        print "\n\n"
        print json.dumps(converter.slug_corrections, indent=4, sort_keys=True)
        print "\n\n"
