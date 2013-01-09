import re 
import sys

from optparse import make_option

from django.core.management.base import BaseCommand
from core import models

class Command(BaseCommand):
    """
    Go through all the aspirants and ensure that if the party they are
    representing is in a coalition then they are also have an aspirant position
    created for the coalition.
    """

    help = 'Create coalition positions'

    # This assumes that a party will only belong to one coalition... Let's hope
    # that is the case...
    party_to_coalition_mapping = {

        # Amani
        'KANU': 'amani', # Kenya African National Union        
        'NFK':  'amani', # New Ford Kenya
        'UDF':  'amani', # United Democratic Forum Party (UDFP)

        # CORD
        'CCU':        'cord', # Chama Cha Uzalendo
        'ford-kenya': 'cord', # Ford Kenya
        'kadu-asili': 'cord', # Kenya African Democratic Union - Asili
        'KSC':        'cord', # Kenya Social Congress
        'mdm':        'cord', # Muungano Development Movement Party (MDM)
        'MDM':        'cord', # Muungano Development Movement Party of Kenya
        'msm':        'cord', # Mkenya Solidarity Movement
        'odm':        'cord', # Orange Democratic Movement
        'P-D-P':      'cord', # People\'s Democratic Party (PDP)
        'TIP':        'cord', # The Independent Party
        'WDM-K':      'cord', # Wiper democratic Movement Kenya

        # Eagle
        'KNC': 'eagle', # Kenya National Congress
        'POA': 'eagle', # Party of Action

        # jubilee
        'TNA':  'jubilee', # The National Alliance (TNA)
        'URP':  'jubilee', # United Republican Party (URP)
        'NARC': 'jubilee', # National Rainbow Coalition

        # not in any coalition
        'adp': '', # Allied Democratic Party of Kenya
        'aford-k': '', # Alliance for the Restoration of Democracy in Kenya
        'agano': '', # AGANO Part
        'AP': '', # Agano Party
        'APK': '', # Alliance Party of Kenya (APK)
        'bdpk': '', # Bright Dawn Party of Kenya
        'ccm': '', # Chama Cha Majimbo na Mwangaza
        'CCM': '', # Chama Cha Mwananchi
        'ccumma': '', # Chama Cha Uma Party
        'cdp': '', # Community Development Party of Kenya
        'cdpk': '', # Communal Democracy Party of Kenya
        'cdu': '', # Conquerors Democratic Union
        'commonwealth': '', # Commonwealth Development Party of Kenya
        'CP': '', # Conservative Party
        'cplp': '', # Common Peoples Liberation Party
        'dap': '', # Democratic Assistance Party
        'dawa': '', # Daraja Ya Wakenya Political Party
        'dcp': '', # Democratic Community Party
        'ddp': '', # Democratic Development Party of Kenya
        'dlpk': '', # Democratic Labour Party of Kenya
        'dna': '', # Democratic National Alliance
        'DP': '', # Democratic Party
        'drp': '', # Democratic Representative Party
        'drpk': '', # Democratic Reformation Party of Kenya
        'dwapk': '', # Development and Welfare Alliance Party of Kenya
        'eakulima': '', # Wakulima Party of Kenya
        'ffr': '', # Forum for Republican Party
        'fodc': '', # Forum for Orange Democratic Change
        'ford': '', # Forum For The Restoration Of Democracy
        'ford-asili': '', # Ford Asili
        'ford-k': '', # Forum For The Restoration Of Democracy - Kenya
        'FORD-P': '', # Ford People
        'forum-restoration-and-democracy-people': '', # Forum for Restoration and Democracy- People
        'FP': '', # Farmers Party
        'fpk': '', # Freedom Party of Kenya
        'FPK': '', # Federal Party of Kenya
        'gap': '', # Green African Party
        'gapk': '', # Generations Alliance Party of Kenya
        'gdp': '', # Growth and Development Party
        'GNU': '', # Grand National Union
        'grdp': '', # Grass Roots Development Party
        'independent': '', # Independent
        'jubile': '', # Jubilee Peoples Party of Kenya
        'kaddu': '', # Kenya African Democratic Development Union
        'kca': '', # Kenya Cultural Alliance
        'kcc': '', # Kenya Citizens Congress
        'kenda': '', # Kenya National Democratic Alliance
        'kenya-african-democratic-union-kadu': '', # Kenya African Democratic Union (KADU)
        'kenya-alliance': '', # Kenya Alliance for National Unity
        'knlpt': '', # Kenya National Liberation Party
        'knpdp': '', # Kenya Nationalist Peoples Democratic Party
        'kpc': '', # Kenya Political Caucus
        'kpcp': '', # Kenya Peoples Convention Party
        'kpk': '', # Kifagio Party of Kenya
        'kpp': '', # Kenya Peoples Party
        'kptp': '', # Kenya Patriotic Trust Party
        'krrp': '', # Kenya Republican Reformation Party
        'ksp': '', # Kenya Socialist Party
        'kunap': '', # Kenya Union of National Alliance for Peace
        'kypc': '', # Kenya Youth Political Caucus
        'lack': '', # Liberal Alliance Coalition of Kenya
        'ldm': '', # Liberal Democratic Movement
        'ldp': '', # Liberal Democratic Party
        'lpk': '', # Labour Party Of Kenya
        'makadara': '', # Madaraka Party
        'mass': '', # Mass Party of Kenya
        'mdapk': '', # Movement for Democratic Advancement Party of Kenya
        'MDP': '', # Maendeleo Democratic Party (MDP)
        'me-katalili-revolutionary-movement-mekaremo': '', # Me Katalili revolutionary movement (MEKAREMO)
        'MGPK': '', # Mazingira Greens Party of Kenya
        'mip': '', # Moral Integrity Party
        'mwangaza-party-mp': '', # Mwangaza Party (MP)
        'nairobi-peoples-convention-party': '', # Nairobi People’s Convention Party
        'nak': '', # National Alliance Of Kenya
        'nap': '', # New Aspiration Party
        'N-A-P': '', # National Alliance Party of Kenya (NAP)
        'NAPK': '', # National Agenda Party of Kenya (NAPK)
        'NAP-K': '', # National Agenda Party of Kenya
        'narc-k': '', # NARC - Kenya
        'national-development-party-ndp': '', # National Development Party (NDP)
        'ND': '', # New Democrats
        'nda': '', # National Democratic Alliance
        'ndc': '', # National Democratic Congress
        'NDM': '', # National Democratic Movement
        'ndp': '', # National Democratic Party
        'new-kanu': '', # New Kanu Alliance Party of Kenya
        'new-sisi': '', # New Sisi Kwa Sisi Kenya
        'nip': '', # National Integrity Party
        'nipk': '', # National Integration Party of Kenya
        'n-liberation': '', # National Liberation Party
        'NLP': '', # National Labour Party
        'none': '', # [None]
        'npdp': '', # New Peoples Democratic Party
        'npk': '', # National Party Of Kenya
        'npp': '', # National Progressive Party
        'nppk': '', # National Patriotic Party of Kenya
        'nrgp': '', # New Revival Generation Party
        'nrp': '', # National Republican Party
        'nrpp': '', # National Renewal Peoples Party
        'nspk': '', # National Star Party of Kenya
        'nuru': '', # Nuru Party
        'nvp': '', # The National Vision Party (NVP)
        'odm-k': '', # Orange Democratic Movement Party Of Kenya
        'paa': '', # Pan Africa Assemblies
        'pambazuka': '', # Pambazuka Party of Kenya
        'papk': '', # Peoples Action Party of Kenya
        'parm': '', # Pan African Reparations Movement
        'pcdpk': '', # Peoples choice Democratic Party of Kenya
        'pdp': '', # Peoples Democratic Party Traditional
        'PDU': '', # Party of Democratic Unity
        'pduk': '', # Peoples Democratic Union of Kenya
        'pecd': '', # Party for Economic Change and Democracy
        'peda': '', # Patriotic Economic Democratic Alliance
        'pick': '', # Party of Independent Candidates of Kenya (PICK)
        'pndp': '', # Party for Negotiated Democracy and Philanthropy
        'PNU': '', # Party of National Unity
        'POH': '', # Party of Hope
        'ppfp': '', # Peoples Party for Progress
        'PPK': '', # Peoples Party of Kenya
        'pppk': '', # Peoples Patriotic Party of Kenya
        'progressive': '', # Progressive Party of Kenya
        'psuk': '', # The Peoples Solidarity Union of Kenya
        'rainbow': '', # Rainbow Orange Alliance Party
        'rap': '', # Republican Alliance Party
        'rap-k': '', # Republican Party of Kenya
        'RBK': '', # RESTORE AND BUILD KENYA (RBK)
        'rdk': '', # Restoration Democrats of Kenya
        'rdp': '', # Rainbow Democratic Party
        'rlp': '', # Republican Liberty Party
        'rpk': '', # Reform Party of Kenya
        'saba-saba': '', # SabaSaba Asili Party
        'SAFINA': '', # Safina Party Of Kenya
        'SDP': '', # Social Democratic Party of Kenya
        'sdp-k': '', # Social Democratic Party
        'sheda': '', # The Sheda Kenya Party
        'shirikisho': '', # Shirikisho Party Of Kenya
        'sisi': '', # Sisi Kwa Sisi
        'spark': '', # Social Party for Advancement and Reforms-Kenya
        'sppc': '', # Social Peoples Party and Congress
        'tkp': '', # Tsadiq Kenya Party
        'ucn': '', # United Centrist National
        'UDM': '', # United Democratic Movement
        'udpik': '', # United Democrats of Peace and Integrity in Kenya
        'ukcp': '', # United Kenya Citizen Party
        'universal-dp': '', # Universal Democratic Party of Kenya
        'uod': '', # Union of Democrats
        'uodp': '', # Union of Democratic Party
        'upc': '', # United Peoples Congress
        'UPK': '', # Unity Party of Kenya
        'upp': '', # United Peoples Party
        'uppk': '', # United Patriotic Party of Kenya
        'vipa': '', # VIPA Progressive Alliance
        'wazalendo': '', # Wazalendo Party
        'wcp': '', # Workers Congress of Kenya
    }

    def handle(self, **options):

        pass