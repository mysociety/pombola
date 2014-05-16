import urlparse

def make_pa_url(pombola_object, base_url):
    parsed_url = list(urlparse.urlparse(base_url))
    parsed_url[2] = pombola_object.get_absolute_url()
    return urlparse.urlunparse(parsed_url)

def add_extra_popolo_data_for_person(person, popolo_object, base_url):
    popolo_object['pa_url'] = make_pa_url(person, base_url)

def add_extra_popolo_data_for_organization(organisation, popolo_object, base_url):
    popolo_object['pa_url'] = make_pa_url(organisation, base_url)
