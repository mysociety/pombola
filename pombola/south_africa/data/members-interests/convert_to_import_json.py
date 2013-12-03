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
os.environ['DJANGO_SETTINGS_MODULE'] = 'pombola.settings'

from django.conf import settings
from django.template.defaultfilters import slugify

from pombola.core.models import Person

class Converter(object):

    groupings = []

    slug_corrections = {
        "amos-matila": "amos-gerald-matila",
        "andre-gaum": "andre-hurtley-gaum",
        "anton-alberts": "anton-de-waal-alberts",
        "archibold-mzuvukile-figlan": "a-m-figlan",
        "archibold-nyambi": "archibold-jomo-nyambi",
        "arthur-ainslie": "arthur-roy-ainslie",
        "bafunani-aaron-mnguni": "bafumani-aaron-mnguni",
        "bertha-mabe": "bertha-peace-mabe",
        "beryl-ferguson": "beryl-delores-ferguson",
        "beverley-lynnette-abrahams": "beverley-lynette-abrahams",
        "bhekizizwe-abram-radebe": "bhekiziswe-abram-radebe",
        "bonisile-alfred-nesi": "bonisile-nesi",
        "busisiwe-mncube": "busisiwe-veronica-mncube",
        "buyiswa-diemu": "buyiswa-cornelia-diemu",
        "charel-de-beer": "charel-jacobus-de-beer",
        "constance-mosimane": "constance-kedibone-kelekegile-mosimane",
        "cq-madlopha": "celiwe-qhamkile-madlopha",
        "crosby-mpozo-moni": "crosby-mpoxo-moni",
        "dalitha-boshigo": "dalitha-fiki-boshigo",
        "danny-montsitsi": "sediane-danny-montsitsi",
        "dennis-bloem": "dennis-victor-bloem",
        "dennis-gamede": "dumisani-dennis-gamede",
        "dirk-feldman": "dirk-benjamin-feldman",
        "dj-stubbe": "dirk-jan-stubbe",
        "doris-nompendlko-ngcengwane": "nompendlko-doris-ngcengwane",
        "dudu-chili": "dudu-olive-chili",
        "duduzile-sibiya": "dudu-sibiya",
        "dumisani-ximbi": "dumsani-livingstone-ximbi",
        "ebrahim-ebrahim": "ebrahim-ismail-ebrahim",
        "elza-van-lingen": "elizabeth-christina-van-lingen",
        "enoch-godongwana": "e-godongwana",
        "ernst-eloff": "ernst-hendrik-eloff",
        "faith-bikani": "faith-claudine-bikani",
        "gbd-mcintosh": "graham-brian-douglas-mc-intosh",
        "gelana-sindane": "gelana-sarian-sindane",
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
        "lemias-buoang-mashile": "budang-lemias-mashile",
        "leonard-ramatlakana": "leonard-ramatlakane",
        "liezl-van-der-merwe": "liezl-linda-van-der-merwe",
        "lulama-mary-theresa-xingwana": "lulama-marytheresa-xingwana",
        "lusizo-makhubela-mashele": "lusizo-sharon-makhubela-mashele",
        "lydia-sindiswe-chikunga": "lydia-sindisiwe-chikunga",
        "mafemane-makhubela": "mafemane-wilson-makhubela",
        "maite-emely-nkoana-mashabane": "maite-emily-nkoana-mashabane",
        "makgathatso-pilane-majake": "makgathatso-charlotte-chana-pilane-majake",
        "makone-collen-maine": "mokoane-collen-maine",
        "mandlenkosi-enock-mbili": "m-e-mbili",
        "mark-harvey-steele": "m-h-steele",
        "mary-anne-lindelwa-dunjwa": "mary-ann-lindelwa-dunjwa",
        "masefako-dikgale": "masefako-clarah-digkale",
        "matome-mokgobi": "matome-humphrey-mokgobi",
        "mavis-nontsikelelo-magazi": "n-m-magazi",
        "mavis-ntebaleng-matladi": "m-n-matladi",
        "mbuyiselo-jacobs": "mbuyiselo-patrick-jacobs",
        "meriam-phaliso": "meriam-nozibonelo-phaliso",
        "michael-de-villiers": "michael-jacobs-roland-de-villiers",
        "michael-james-ellis": "m-j-ellis",
        "mmatlala-boroto": "mmatlala-grace-boroto",
        "mninwa-mahlangu": "mninwa-johannes-mahlangu",
        "mntombizodwa-florence-nyanda": "n-f-nyanda",
        "mogi-lydia-moshodi": "moji-lydia-moshodi",
        "mohammed-sayedali-shah": "mohammed-rafeek-sayedali-shah",
        "mosie-anthony-cele": "mosie-antony-cele",
        "mpane-mohorosi": "mpane-martha-mohorosi",
        "n-d-ntwanambi": "nosipho-dorothy-ntwanambi",
        "nomzamo-winnie-madikizela-mandela": "nomzamo-winfred-madikizela-mandela",
        "ntombikhayise-nomawisile-sibhidla": "ntombikayise-nomawisile-sibhida",
        "obed-bapela": "kopeng-obed-bapela",
        "onel-de-beer": "onell-de-beer",
        "pakishe-motsoaledi": "pakishe-aaron-motsoaledi",
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
        "sicelo-shiceka": "s-shiceka",
        "siyabonga-cwele": "siyabonga-cyprian-cwele",
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
        "trevor-john-bonhomme": "trevor-bonhomme",
        "tshiwela-elidah-lishivha": "tshiwela-elida-lishivha",
        "velly-manzini": "velly-makasana-manzini",
        "willem-faber": "willem-frederik-faber",
        "zephroma-dubazana": "zephroma-sizani-dubazana",
        "zephroma-sizani-dlamini-dubazana": "zephroma-sizani-dubazana",
        "zisiwe-balindlela": "zisiwe-beauty-nosimo-balindlela",
        "zoliswa-kota-fredericks": "zoliswa-albertina-kota-fredericks",
        "zukiswa-rantho": "daphne-zukiswa-rantho",

        # FIXME - need to manually match these

        # FIXME - can't seem to find a match for these
        "buyiswa-blaai": None,
    }

    def __init__(self, filename):
        self.filename = filename

    def convert(self):
        data = self.extract_data_from_json()

        self.extract_source(data)
        self.extract_entries(data)

        return self.produce_json()

    def extract_source(self, data):
        source_url = data['source']
        year = data['year']

        source_filename = re.sub(r'.*/(.*?)\.pdf', r'\1', source_url)
        source_name = urllib.unquote(source_filename).strip()

        self.source = {
            "name": source_name,
            "date": year + "-01-01",
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
                        entry[key.strip()] = entry.pop(key).strip()

                # Filter out known bad entries
                entries = [ e for e in entries if not (e.get('No') == 'Nothing to disclose') ]

                if len(entries) == 0:
                    continue

                grouping = {
                    "source": self.source,
                    "entries": entries,
                }

                # Break up the name into sort_order and proper name
                sort_order, category_name = raw_category_name.strip().split('. ')
                grouping['category'] = {
                    "sort_order": int(sort_order),
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
            last_name = name.split(' ')[-1]

            possible_persons = Person.objects.filter(legal_name__icontains=last_name)

            # if possible_persons.count() == 1:
            #     possible_slug = possible_persons.all()[0].slug
            #     self.slug_corrections[slug] = possible_slug
            #     return possible_slug

            for person in possible_persons:
                print 'perhaps: "{}": "{}",'.format(slug, person.slug)
            else:
                print "no possible matches for {}".format(slug)

            raise Exception("Slug {} not found, please find matching slug and add it to the slug_corrections".format(slug))

    def produce_json(self):
        data = self.groupings
        out = json.dumps(data, indent=4, sort_keys=True)
        return re.sub(r' *$', '', out, flags=re.M)

    def extract_data_from_json(self):
        with open(self.filename) as fh:
            return json.load(fh)


if __name__ == "__main__":
    converter = Converter(sys.argv[1])
    output = converter.convert()
    # print json.dumps(converter.slug_corrections, indent=4, sort_keys=True)
    print output
