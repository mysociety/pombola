# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

from collections import defaultdict
import csv
from os.path import dirname, join
import re

from pombola.core.models import ParliamentarySession, PlaceKind

from mapit.models import Area, Geometry, NameType, Type

from django.contrib.gis.geos import GEOSGeometry
from django.core.management import BaseCommand
from django.db import transaction
from django.utils.text import slugify

# This script will recreate the Federal Constituency boundaries based
# on LGA areas, which were imported from GADM.  This is needed because
# the current Federal Constituency boundaries in MapIt appear to be
# hopelessly wrong, as if they were created from the wrong LGAs in the
# first place.  This also attempts to improve the MapIt area name (to
# match that in the ShineYourEye "Political Atlas" spreadsheet, while
# preserving the original MapIt name as a separate name type for each
# area).

class NoAreaFound(Exception):
    pass


class AmbiguousAreaName(Exception):
    pass


# There's a good list of Federal Constituency names and states here
# for comparison:
#
#    http://www.inecnigeria.org/wp-content/uploads/2015/05/2015-UPDATED-ELECTED-REPS-MEMBERS-ELECTED-ONLY-10.04.15.xlsx

atlas_to_mapit_names = {
    ("ABUA-ODUAL/AHOADA EAST", "Rivers"): "Ahoada East/Abua/Odual",
    ("ADO EKITI/IREPODUN/IFELODUN", "Ekiti"): "ADO EKITI/IREPODUN-IFELODUN",
    ("ADO-ODO/OTA", "Ogun"): "AdoOdo/Ota / Otta",
    ("AFIJIO/ATIBA/OYO EAST/ OYO WEST", "Oyo"): "Afijio/Atiba East/Oyo West",
    ("AGAIE/LAPAI", "Niger"): "Agale / Lapai",
    ("AGWARA/BORGU", "Niger"): "Agwara / Borgu",
    ("AHOADA WEST/OGBA/EGBEMA/INDONI", "Rivers"): "Ogba/Egbema/Ndoni/Ahoada West",
    ("AKOKO NORTH EAST/ AKOKO NORTH WEST", "Ondo"): "Akoko North East/North-West",
    ("AKOKO SOUTH EAST/ AKOKO SOUTH WEST", "Ondo"): "Akoko South East/South Wes",
    ("AKUKU-TORU/ASARI-TORU", "Rivers"): "Akuku - Toru/Asari - Toru",
    ("AKURE NORTH/AKURE SOUTH", "Ondo"): "Akure South / North",
    ("AKWANGA//WAMBA/NASARAWA EGGON", "Nassarawa"): "AKWANGA/WAMBA/NASARAWA EGGON",
    ("ALIERO/GWANDU/JEGA", "Kebbi"): "Aliero",
    ("AMUWO-ODOFIN", "Lagos"): "Amuwo Odofin Federal Constituency",
    ("ANDONI/OPOBO-NKORO", "Rivers"): "Opobo / Nkoro",
    ("ANKA//TALATA-MAFARA", "Zamfara"): "Anka/Talata Mafara",
    ("ANKPA/OMALA/OLAMABORO", "Kogi"): "Ankpa-Omala-Olamaboro",
    ("APAPA", "Lagos"): "Apapa Federal Constituency",
    ("ARDO-KOLA/LAU/KARIM-LAMIDO", "Taraba"): "Lau/K/Lamido/Ardo-Kola",
    ("ATAKUNMOSA EAST/WEST/ILESHA EAST/WEST", "Osun"): "Atakumosa / East/ West & Ilesa East /West",
    ("AYEDAADE/IREWOLE/ISOKAN", "Osun"): "Ayedaade / Irewole / Isokan",
    ("AYEDIRE/IWO/OLA-OLUWA", "Osun"): "Ayedire / Iwo / Ola-Oluwa",
    ("Aba North/South", "Abia"): "Aba North / Aba South",
    ("Abaji/Gwagwalada/Kwali/Kuje", "Federal Capital Territory"): "Gwagwala/Kuje",
    ("Abak/ETIM EKPO/IKA", "Akwa Ibom"): "Abak/Etim Ekpo & Ika",
    ("Aboh Mbaise/Ngor Okpala", "Imo"): "Aboh Mbaise/Ngor Okpala Federal Consistuency",
    ("Ado/Ogbadigba/Okpokwu", "Benue"): "ADO/OGBADIBO/OKPOKWU",
    ("Aguta", "Anambra"): "Aguata",
    ("Ahiazu Mbaise/Ezinihitte", "Imo"): "AHIAZU-MBAISE/EZINITTE",
    ("Akpabuyo/Bakassi/Calabar South", "Cross River"): "Calabar South/Akpabuyo/Bakassi",
    ("Anaocha/Njikoka/Dunukofia", "Anambra"): "Anocha/Njikoka/Dunukofia",
    ("Aninri/Agwu/Oji-uzo", "Enugu"): "Aninri / Agwu / Oji-River",
    ("Aniocha North/South", "Delta"): "Aniocha North/Aniocha South/Oshimili North/Oshimili South",
    ("Apa/Aguta", "Benue"): "APA/AGATU",
    ("Askira-Uba/Hawul", "Borno"): "Askira /Uba / Hawul",
    ("Awka North/South", "Anambra"): "Awka North & South",
    ("BAGUDO/SURU", "Kebbi"): "Bagudo / Suru",
    ("BAKORI/DANJA", "Katsina"): "Bakoro/Danja",
    ("BARKIN LADI/RIYOM", "Plateau"): "Barakin-Ladi/Riyom",
    ("BARUTEN/KAIAMA", "Kwara"): "Baruten/Kalama",
    ("BATAGARAWA/RIMI/CHARANCHI", "Katsina"): "BATAGARA/CHARANGI/RIMI",
    ("BOGORO/ DASS/ TAFAWA BALEWA", "Bauchi"): "Bogoro/Dass/Tafawa-B",
    ("BOLUWADURO/IFEDAYO/ILA", "Osun"): "Boluwaduro / Ifedayo / Ila",
    ("BONNY/DEGEMA", "Rivers"): "Degema/Bonny",
    ("BOOSO/PAIKORO", "Niger"): "Bosso/Paikoro",
    ("Balanga/Billiri", "Gombe"): "Balanga/Biliri",
    ("Bama/Ngala/Kala-Balge", "Borno"): "Bama / Ngala",
    ("Bebeji/Kiru", "Kano"): "Kiru/Bebeji",
    ("Bekwarra/Obudu/Obanliku", "Cross River"): "Obanliku/OBUDU/BEKWARRA",
    ("Birnin-Gwari/Giwa", "Kaduna"): "Giwa/Birnin-Gwari",
    ("Birniwa/Guri/Kiri-Kasamma", "Jigawa"): "BIRNIWA/GURI/KIRIKASAMMA",
    ("Biu/Bayo/Shani/Kwaya Kusar", "Borno"): "Biu / Bayo / Kwaya-Kusar / Shani",
    ("Brass/Nembe", "Bayelsa"): "Brass / Nembe",
    ("Calabar Munincipal/Odukpani", "Cross River"): "CALABAR/UDOKPANI",
    ("Chikun/Kajuru", "Kaduna"): "Kajuru/Chikum",
    ("DANDUME/FUNTUA", "Katsina"): "Funtua/Dandume Constituency",
    ("DANGE SHUNI/BODINGA/TURETA", "Sokoto"): "Dange-Shuni/Bodinga/Tureta",
    ("DAURA/MAI'ADUA/SANDAMU", "Katsina"): "Daura/Maiduwa/Sadamu Constituency",
    ("DEKINA/BASSA", "Kogi"): "Bassa / Dekina",
    ("Dambatta/Makoda", "Kano"): "Dabbatta/Makoda",
    ("Damboa/Gwoza/Chibok", "Borno"): "Damibo'a / Chibok/ Gwoza",
    ("Dikwa/Mafa/Konduga", "Borno"): "Mafa/Dikwa/Konduga",
    ("Dukku / Nafada", "Gombe"): "Dukku/Nafada",
    ("EDE NORTH/EDE SOUTH/EGBEDORE/EJIGBO", "Osun"): "Eden North",
    ("EGBADO-NORTH/IMEKO-AFON", "Ogun"): "Egbado North/Imeko Afon",
    ("EGBADO-SOUTH/IPOKIA", "Ogun"): "Egbado South/Ipokia",
    ("EGBEDA/ONA-ARA", "Oyo"): "Egbeda/ Ona-Ara",
    ("EKITI SOUTH WEST/IKERE/ORUN ISE", "Ekiti"): "Ekiti South West/IKERE/ISE -ORUN",
    ("EKITI/IREPODUN/ISIN/OKE-ERO", "Kwara"): "Isin/Irepodun/Ekiti & Oke-Ero",
    ("EMURE/GBOYIN/EKITI EAST", "Ekiti"): "EMURE/GBONYIN/EKITI EAST",
    ("ETCHE/OMUMA", "Rivers"): "Etche / Omuma",
    ("Egor/Ikpoba-okha", "Edo"): "Egor / Ikpoba-Okha",
    ("Ehimembano/Ihitte Uboma/Obowo", "Imo"): "Ehime-Mb/Ihitte/U/OBONO",
    ("Eket/Onna/Esit/eket/ibeno", "Akwa Ibom"): "Eket/Onna/Esit Eket/Ibeno",
    ("Enugu East/Isi-Uzo", "Enugu"): "Enugu_East / Isi-Uzo",
    ("Enugu North/South", "Enugu"): "Enugu North/Enugu South",
    ("Esan Central/West/Igueben", "Edo"): "Esan Central",
    ("Esan North-East/Esan South- East", "Edo"): "Esan North East/South West",
    ("Etinan/ nsit/nsit Ubium", "Akwa Ibom"): "Etinan",
    ("Etsako East/West/Central", "Edo"): "Etsako",
    ("Ezza North/Ishielu", "Ebonyi"): "Ezza North/Ishelu",
    ("GADA/GORONYO", "Sokoto"): "Goronyo/Gada",
    ("GBAKO/BIDA/KATCHA", "Niger"): "Bida Gbaka Paicho",
    ("GULANI/GUJBA/DAMATURU/TARMUWA", "Yobe"): "Damatura/Gujba/Gulani/Tarmuwa",
    ("Ganye/Mayo Belwa/Toungo/JADA", "Adamawa"): "Mayo Belwa/Jada/Ganye/Toongo",
    ("Gombe/kwami/Funakaye", "Gombe"): "Gombe Kwami Funakaye",
    ("Gwarzo/kabo", "Kano"): "Gwarzo/kabo Federal Constituency",
    ("Gwer-East/Gwer-West", "Benue"): "Gwer East/Gwer West",
    ("Hadejia/Kafin Hausa/Auyo", "Jigawa"): "Hadejia/KafinHau",
    ("Hong/Gombi", "Adamawa"): "Gombi/Hong",
    ("IBADAN NORTH EAST/IBADAN SOUTH EAST", "Oyo"): "Ibadan N.East / South East",
    ("IBADAN NORTH WEST/SOUTH WEST", "Oyo"): "Ibadan Southwest/ Northwest",
    ("IBARAPA CENTRAL/IBARAPA NORTH", "Oyo"): "Ibarapa Central/North",
    ("IBARAPA EAST/IDO", "Oyo"): "Ibarapa East / Ido",
    ("IBEJU-LEKKI", "Lagos"): "IJEBU - LEKKI",
    ("IDANRE/IFEDORE", "Ondo"): "Idanre / Ifedore",
    ("IFAKO-IJAIYE", "Lagos"): "Ifako Ijaye",
    ("IFE CENTRAL/ IFE EAST/ IFE NORTH/ IFE SOUTH", "Osun"): "Ife Federal Constituency",
    ("IFO/EWEKORO", "Ogun"): "Ifo / Ewekoro",
    ("IJERO/EKITI WEST/ EFON", "Ekiti"): "IJERO/EFON/EKITI WEST",
    ("IFELODUN/OFFA/OYUN", "Kwara"): "Felodun/Offa/Oyun",
    ("IJEBU ODE/ODOGBOLU/ IJEBU NORTH EAST", "Ogun"): "Ijebu Central",
    ("IJEBU-EAST/IJEBU-NORTH/OGUN-WATERSIDE", "Ogun"): "Ogun Waterside/Ijebu North /East",
    ("IKENNE/SHAGAMU/REMO NORTH", "Ogun"): "Sagamu/Ikenne / Remo North",
    ("IKOLE/OYE", "Ekiti"): "Ekiti North",
    ("ILAJE/ESEODO", "Ondo"): "Ilaje / Ese Odo",
    ("ILELLA/GWADABAWA", "Sokoto"): "ILLELA/GWADABAWA",
    ("ILEOLUJI - OKEIGBO /ODIGBO", "Ondo"): "Ile - Oluji/Okeigbo & Odigbo",
    ("ILORIN SOUTH/ EAST", "Kwara"): "Ilorin East/Ilorin South",
    ("IREPODUN/OLORUNDA/OSOGBO/OROLU", "Osun"): "Irepodun / Olorunda / Orolu / Osogbo",
    ("ISA/SABON BIRNI", "Sokoto"): "Isa/S.Birni",
    ("ISEYIN/ITESIWAJU/KAJOLA/IWAJOWA", "Oyo"): "Iseyin/ Itesiwasu / Kajola / Iwajowa",
    ("Idah/Igalamela-Odolu/Ibaji/Ofu", "Kogi"): "IDAH/IGALAMELA/IBAJI/OFU",
    ("Ideato North /South", "Imo"): "IDEATO NORTH/SOUTH",
    ("Idemili North/South", "Anambra"): "Idemili North/Idemili South",
    ("IDO-OSI/MOBA/ILEJEMEJE", "Ekiti"): "EKITI II",
    ("Igbo-Etiti/Uzo-Uwani", "Enugu"): "Igbo Etiti",
    ("Ika", "Delta"): "Ikan North-East",
    ("Ikara/Kubau", "Kaduna"): "Ikara/KuKubau",
    ("Ikom/Boki", "Cross River"): "Boki/Ikom",
    ("Ikono/ Ini", "Akwa Ibom"): "Ini /Ikono",
    ("Ikot Abasi/MKPAT ENIN/EASTERN OBOLO", "Akwa Ibom"): "Ikot Abasi",
    ("Ikot Ekpene/ Essien Udim/ Obot Akara", "Akwa Ibom"): "Ikot Ekpene",
    ("Ikwo/Ezza South", "Ebonyi"): "IKwo / Ezza South",
    ("Ikwuano/Umuahia North/South", "Abia"): "Umahia North/South/Ikwuaro",
    ("Isiala Ngwa North/South", "Abia"): "Isala Ngwa North/south",
    ("Isoko North/South", "Delta"): "Isoko North/Isoko South",
    ("Isuikwato/Umunneochi", "Abia"): "Isuikwua/Umunneochi",
    ("Itu/Ibiono Ibom", "Akwa Ibom"): "Itu",
    ("Ivo/Ohaozara/Onicha", "Ebonyi"): "Ohaozara/Onicha/Ivo",
    ("JALINGO/ YORRO/ ZING", "Taraba"): "Jalingo / Yorro / Zing",
    ("JIBIA/KAITA", "Katsina"): "Kaita/Jibiya Constituency",
    ("JOS NORTH/BASSA", "Plateau"): "Jos North/Bassa Federal Constituency",
    ("Jama'are/itas-gadau", "Bauchi"): "JAMAARE/ITAS-GADAU",
    ("Jema'a/Sanga", "Kaduna"): "Jema'a /Sanga",
    ("KABBA-BUNU/IJUMU", "Kogi"): "KABBA-BUNU/IJIMU",
    ("KALGO/BUNZA/BIRNIN KEBBI", "Kebbi"): "Birnin Kebbi - Kalgo - Bunza",
    ("KANKARA/FASKARI/SABUWA", "Katsina"): "Kankara/Faskari/Sabuwa Constituency",
    ("KANKIA/KUSADA/INGAWA", "Katsina"): "Kankia/Kusada/ Ingawa Federal Constituency",
    ("KATSINA", "Katsina"): "Katsina Federal Constituency",
    ("KAURA-NAMODA/BIRNIN MAGAJI", "Zamfara"): "KAURA - NAMODA/BIRNIN MAGAJI",
    ("KEFFI/KARU/KOKONA", "Nassarawa"): "Karu / Kokona / Keffi",
    ("KHANA/GOKANA", "Rivers"): "Khana / Gokana",
    ("KOKO-BESSE/MAIYAMA", "Kebbi"): "Maiyama/koko - Besse",
    ("KOSOFE", "Lagos"): "Kosofe Federal Constituency",
    ("Kachia/Kagarko", "Kaduna"): "Kachiya/Kagarko",
    ("Kaga/Gubio/Magumeri", "Borno"): "Kaga / Gubio / Magumeri",
    ("Katsina-Ala/Ukum/Logo", "Benue"): "Katsina-Ala Ukum Logo",
    ("Kazaure/Roni/Gwiwa/Yankwashi", "Jigawa"): "Kazaure/Roni Gwiwa",
    ("Kukawa/Mobbar/Abadam/Guzamala", "Borno"): "Kukawa/Guzamala Abadam/Mobbar",
    ("Kumbosto", "Kano"): "Kumbotso",
    ("Kura/Madobi/Garun Mallam", "Kano"): "Kura/Madobi/Garum Mallam",
    ("LAGOS ISLAND I", "Lagos"): "LagosIsland I Federal Constituency",
    ("LAFIA/OBI", "Nassarawa"): "Lafia  / Obi",
    ("LOKOJA/KOGI (KK)", "Kogi"): "Lokoja",
    ("MACHINA/ NGURU/ KARASUWA/YUSUFARI", "Yobe"): "Machina/Nguru/Karasuwa/Yusufari",
    ("MALUMFASHI/KAFUR", "Katsina"): "Malunfashi/Kafur",
    ("MANI/BINDAWA", "Katsina"): "Mani/Bindawa Constituency",
    ("MARADUN/BAKURA", "Zamfara"): "Bakura/Maradun",
    ("MARU/BUNGUDU", "Zamfara"): "Bungudu/Maru",
    ("MASHI/DUTSI", "Katsina"): "Mashi/Dutsi Constituency",
    ("MOKWA/LAVUN/EDATI", "Niger"): "Lavvn/Edati/Mokwa",
    ("MUSHIN I", "Lagos"): "Mushin I Federal Constituency",
    ("MUSHIN II", "Lagos"): "Mushin II Federal Constituency",
    ("Maiduguri (Metropolitan)", "Borno"): "Maiduguri",
    ("Mallam Madori/Kaugama", "Jigawa"): "MalamMad/Kaugama",
    ("Mbaitolu/Ikeduru", "Imo"): "Mbaitoli/Ikeduru",
    ("Michika/Madagali", "Adamawa"): "Madagali / Michika",
    ("Minjibir/Ungogo", "Kano"): "Ungogo/Minjibir",
    ("Misau/Damban", "Bauchi"): "Misau/ Dambam",
    ("Monguno/Marte/Nganzai", "Borno"): "Marte & Monhuno & Nganzai",
    ("Mubi North/Mu South/Maiha", "Adamawa"): "Mubi North / Mubi South / Maiha",
    ("Municipal", "Kano"): "Kano Municipal",
    ("Municipal/Bwari", "Federal Capital Territory"): "ABUJA MUNICIPAL/BWARI",
    ("NASSAWARA/TOTO", "Nassarawa"): "Nasarawa / Toto",
    ("Ndokwa/Ukwani", "Delta"): "Ndokwa East/Ndokwa",
    ("Nnewi North/South/Ekwusigo", "Anambra"): "NnewiNort / South & Ekwusigo",
    ("Nsukka/ Igboeze South", "Enugu"): "Nsukka/Igboeze",
    ("Nwangele/Isu/Njaba/Nkwerre", "Imo"): "NKWERRE/NWANGELE/ISU/NJABA",
    ("OBIO AKPOR", "Rivers"): "Obio-Akpor",
    ("OBOKUN/ORIADE", "Osun"): "Oriade / Obokon",
    ("ODEDA/OBAFEMI-OWODE/ABEOKUTA NORTH", "Ogun"): "Abeokuta North / Obafemi Owode & Odeda Fed. Const.",
    ("ODO-OTIN/IFELODUN/BORIPE", "Osun"): "Osun Central II (Odo-Otin / Ifelodun / Boripe",
    ("OGBOMOSHO NORTH/OGBOMOSO SOUTH /ORIRE", "Oyo"): "Ogbomosho North & South/Orire",
    ("OGO-OLUWA/SURULERE", "Oyo"): "Ogo Oluwa / Surulere",
    ("OKENE/OGORI MAGONGO", "Kogi"): "OKENE/OGORI-MAGONGO",
    ("OKRIKA/OGU-BOLO", "Rivers"): "Okrika / Ogu / Bolo",
    ("ONDO WEST/ONDO EAST", "Ondo"): "ONDO EAST/WEST",
    ("OSHODI/ISOLO I", "Lagos"): "Oshodi-Isolo I Federal Constituency",
    ("OSHODI/ISOLO II", "Lagos"): "Oshodi / Isolo Fed. Const II",
    ("Obingwa/Osisioma/Ugwunagbo", "Abia"): "Obingwa/osisioma/Ugwumagbo",
    ("Ohaji-Egbema/Oguta/Oru West", "Imo"): "Ohaji / Egbema-Oguta-Oru West",
    ("Ohaukwu/Ebonyi", "Ebonyi"): "Ebonyi/Ohaukwu",
    ("Oju/Obi", "Benue"): "Oju / Obi",
    ("Okigwe/Isiala-Mbano/Onuimo", "Imo"): "Onuimo/Okigwe/Isiala Mbano",
    ("Okpe/Sapele/Uvwie", "Delta"): "Okpe/ Sapele/ Uvwie",
    ("Onitsha North/South", "Anambra"): "Onitsha North/South Federal",
    ("Orlu/Oru East/Orsu", "Imo"): "ORLU/ORSU/ORUE AST",
    ("Oron/Mbo/Okobo/UrueOffong/Oruko/Udung-Uko", "Akwa Ibom"): "Oron/Mbo/Okobo/Urefong/udung-Uko",
    ("Orumba North/South", "Anambra"): "Orumba South",
    ("Ovia South-West/Ovia North-East", "Edo"): "Ovia Federal Constituency",
    ("Owan West/East", "Edo"): "Owan East / West",
    ("Owerri Municipal/Owerri North/West", "Imo"): "OWERRI MINICIPAL/NORTH/WEST",
    ("Oyi/Ayamelum", "Anambra"): "Ayamelum / Oyi",
    ("PANKSHIN/KANAM/ KANKE", "Plateau"): "PANKSHIN/KANKE/KANAM",
    ("PATIGI/EDU/MORO", "Kwara"): "Edu/Moro/Patigi",
    ("PORT HARCOURT I", "Rivers"): "Port Harcourt One",
    ("PORT HARCOURT II", "Rivers"): "Port Harcourt Fed. Const.2",
    ("RIJAU/MAGAMA", "Niger"): "MAGAMA/RIJAU",
    ("Rano/Bunkure/Kibiya", "Kano"): "Rano/Bunkure/Kibiya Constituency",
    ("SAFANA/DANMUSA/ BATSARI", "Katsina"): "SAFANA/DAN-MUSA/BATSARI",
    ("SAKI EAST/ SAKI WEST/ ATISBO", "Oyo"): "Saki East/West/Atisbo",
    ("SHENDAM/MIKANG/QUA'AN-PAN", "Plateau"): "SHENDAMMIKANG/QUAANPAN",
    ("SHINKAFI/ZURMI", "Zamfara"): "ZurmiI/Shinkafi",
    ("SHIRORO/RAFI/MUNYA", "Niger"): "MUNYA/RAFI/SHIRORO",
    ("SHOMOLU", "Lagos"): "Somolu",
    ("SULEJA/TAFA/GURARA", "Niger"): "Gurara/Suleja/Tafa",
    ("SURULERE I", "Lagos"): "Surulere I Federal Constituency",
    ("SURULERE II", "Lagos"): "Surulere Fed. Const. II",
    ("Sule-Tankarkar/Gagarawa/Maigatari/Gumel", "Jigawa"): "Tankarkar/Gagarawa",
    ("TAI/ELEME/OYIGBO", "Rivers"): "Eleme / Oyigbo / Tai",
    ("TAKUM/DONGA/USSA", "Taraba"): "Donga/Ussa/Takum/Special Area",
    ("TAMBUWAL-KEBBE", "Sokoto"): "Kebbe/Tambuwal Federal Constituency",
    ("TSAFE/GUSAU", "Zamfara"): "GUSAU/TSAFE",
    ("Ughelli North/South/Udu", "Delta"): "Udu/Ughelli North/South",
    ("Ukanafun/Oruk anam", "Akwa Ibom"): "Ukanafun/Orukaanam",
    ("Ukwa East/Ukwa West", "Abia"): "Ukwa East/West",
    ("Uyo/Uruan/Nsit Ata/Ibeskip Asutan", "Akwa Ibom"): "Uyo",
    ("Vandeikya/Konshisha", "Benue"): "Konshisha/Vandekiya",
    ("WUKARI/IBI", "Taraba"): "Ibi/Wukari",
    ("WURNO/RABBAH", "Sokoto"): "Wurno / Rabah",
    ("WUSHISHI/MASHEGU/KONTAGORA/MARIGA", "Niger"): "Kontagora/Wushishi/Mariga/Mashegu",
    ("Warri", "Delta"): "Warri North/Warri South/Warri West",
    ("YAGBA EAST/WEST/MOPAMURO", "Kogi"): "Yagba East/West",
    ("YAURI/NGASKI /SHANGA", "Kebbi"): "Yauri/Shanga/Ngaski",
    ("Yenagoa/Kolokuma/Opokuma", "Bayelsa"): "Yenagoa/K/Opokuma",
    ("Yola North/Yola South/Girei", "Adamawa"): "Yola North/Yola South & Girei",
    ("ZURU/FAKAI/DANKO/SAKABA/WASAGU", "Kebbi"): "Zuru/Fakai/Sakaba/Danko-Wasagu",
    ("Zangon Kataf/Jaba", "Kaduna"): "Jaba/Zangon Kafat",
    ("Zaria Federal", "Kaduna"): "Zaria",
}

# Couldn't find a match for these:
#
#    ("Furore/Song", "Adamawa"): "",
#    ("LAGOS MAINLAND", "Lagos"): "",
#
# Looking up the LGAs "Furore", "Song" and "Mainland" in MapIt, they
# intersect with lots of FED type areas in MapIt; can't easily tell
# which one was originally meant to correspond with. I don't think
# this will matter when we reconstruct the FED areas, though.


class Command(BaseCommand):

    help = "Recreate Federal Constituency boundaries and fix area names"

    def get_mapit_area(self, name, type_code, parent=None, grandparent=None):
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)

        area_kwargs = {'name__iexact': name}
        if parent is not None:
            area_kwargs['parent_area'] = parent
        if grandparent is not None:
            area_kwargs['parent_area__parent_area'] = grandparent
        mapit_type = Type.objects.get(code=type_code)
        areas = list(mapit_type.areas.filter(**area_kwargs))
        if len(areas) > 1:
            msg = 'Ambiguous name / type: {0} ({1})'.format(name, type_code)
            raise AmbiguousAreaName(msg)
        elif len(areas) == 1:
            return areas[0]
        else:
            # No areas found; try the alternative names:
            area_kwargs = {'names__name__iexact': name}
            if parent is not None:
                area_kwargs['parent_area'] = parent
            if grandparent is not None:
                area_kwargs['parent_area__parent_area'] = grandparent
            areas = list(mapit_type.areas.filter(**area_kwargs).distinct())
            if len(areas) > 1:
                msg = 'Ambiguous alt name / type: {0} ({1})'.format(
                    name, type_code
                )
                raise AmbiguousAreaName(msg)
            elif len(areas) == 1:
                return areas[0]
            else:
                msg = 'No name / alt name found for: {0} ({1})'.format(
                    name, type_code
                )
                raise NoAreaFound(msg)

    def handle(self, *args, **options):
        with transaction.atomic():
            self.handle_inner(self, *args, **options)

    def handle_inner(self, *args, **options):

        atlas_name_type, _ = NameType.objects.get_or_create(
            code='atlas',
            defaults={'description': 'Name from the Political Atlas for SYE'},
        )
        old_mapit_name_type, _ = NameType.objects.get_or_create(
            code='old_mapit',
            defaults={'description': 'Original name in MapIt'},
        )
        pombola_place_name_type, _ = NameType.objects.get_or_create(
            code='pombola',
            defaults={'description': 'Place name in Pombola'},
        )

        fed_area_type = Type.objects.get(code='FED')
        fed_place_kind = PlaceKind.objects.get(slug='federal-constituency')
        session = ParliamentarySession.objects.get(slug='hr2011')

        for atlas_tuple, mapit_name in atlas_to_mapit_names.items():
            atlas_fed_name, atlas_state_name = atlas_tuple
            # Check if this area's name has already been fixed:
            area_with_new_name = Area.objects.filter(
                name=atlas_fed_name,
                type__code='FED',
            ).first()
            if area_with_new_name:
                area_already_has_alias = area_with_new_name.names.filter(
                    name=mapit_name,
                    type=old_mapit_name_type,
                ).exists()
                if area_already_has_alias:
                    # Then this area has already been corrected on a
                    # previous run, so skip it:
                    continue
            # Otherwise we have to fix up the names:
            existing_mapit_fed = Area.objects.get(
                name=mapit_name,
                type__code='FED',
            )
            # The original names (and FED data in general) in MapIt
            # are pretty terrible, so keep the existing MapIt name as
            # an existing Name and change the main name of the area to
            # the one from the atlas.
            existing_mapit_fed.names.get_or_create(
                type=old_mapit_name_type,
                name=mapit_name,
            )
            existing_mapit_fed.name = atlas_fed_name
            existing_mapit_fed.save()
            # Also create a Name for the new canonical name:
            existing_mapit_fed.names.get_or_create(
                type=atlas_name_type,
                name=atlas_fed_name,
            )

        # Now go through every row of the spreadsheet, and find the
        # LGAs that should be composed to make the new boundary of the
        # FED area...

        atlas_filename = join(
            dirname(__file__), '..', '..', 'data',
            'Nigeria - Political Atlas for SYE.csv'
        )

        federal_constituencies_to_recreate = defaultdict(set)

        with open(atlas_filename) as f:
            reader = csv.DictReader(f)
            for row in reader:
                state_name = row['STATE NAME']
                mapit_state = self.get_mapit_area(state_name, 'STA')
                # print state_name, '=>', self.get_mapit_area(state_name, 'STA')
                fed_name = row['FEDERAL CONSTITUENCY']
                lga_name = row['LGA NAME']
                try:
                    mapit_fed = self.get_mapit_area(fed_name, 'FED')
                except NoAreaFound:
                    # There are a few we have to create:
                    print("Creating:", fed_name)
                    mapit_fed = Area.objects.create(
                        name=fed_name,
                        type=fed_area_type,
                    )
                    mapit_fed.names.create(
                        type=atlas_name_type,
                        name=fed_name
                    )
                    # Also create a Pombola Place if it's missing:
                    place_slug = slugify(unicode(fed_name))
                    place, _ = fed_place_kind.place_set.get_or_create(
                        slug=place_slug,
                        defaults={
                            'name': fed_name
                        }
                    )
                    place.name = fed_name
                    place.mapit_area = mapit_fed
                    place.parliamentary_session = session
                    place.parent_place = mapit_state.place_set.get()
                    place.save()
                # Record the LGA as being part of the new composition of
                # that FED area:
                mapit_lga = self.get_mapit_area(
                    lga_name,
                    'LGA',
                    grandparent=mapit_state
                )
                federal_constituencies_to_recreate[mapit_fed].add(mapit_lga)
                # Now check that a Pombola Place object already exists
                # for this:
                place_count = mapit_fed.place_set.count()
                if place_count != 1:
                    msg = "Unexpected number of Pombola Places for {0}: {1}"
                    raise Exception(msg.format(mapit_fed, place_count))
                # Add the Pombola place name as another alternative
                # name for the area - the more name variants in MapIt
                # the better, I think.
                place = mapit_fed.place_set.get()
                mapit_fed.names.get_or_create(
                    type=pombola_place_name_type,
                    name=place.name,
                )

        mapit_fed_areas_to_remove = Area.objects.filter(
            type=fed_area_type
        ).exclude(
            id__in=[a.id for a in federal_constituencies_to_recreate.keys()]
        )
        for a in mapit_fed_areas_to_remove:
            print("Removing:", a)
            a.delete()

        for mapit_fed, lga_subareas in federal_constituencies_to_recreate.items():
            mapit_lga_ids = [a.id for a in lga_subareas]
            unioned = Geometry.objects.filter(area__id__in=mapit_lga_ids) \
                .unionagg()
            geos_geometry = GEOSGeometry(unioned).ogr
            mapit_fed.polygons.all().delete()
            if geos_geometry.geom_name == 'POLYGON':
                shapes = [geos_geometry]
            else:
                shapes = geos_geometry
            for shape in shapes:
                mapit_fed.polygons.create(polygon=shape.wkb)
