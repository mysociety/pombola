def fix_province_name(province_name):
    if province_name == 'Kwa-Zulu Natal':
        return 'KwaZulu-Natal'
    else:
        return province_name


def fix_municipality_name(municipality_name):
    if municipality_name == 'Merafong':
        return 'Merafong City'
    else:
        return municipality_name
