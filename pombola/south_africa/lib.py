import urlparse

def make_pa_url(pombola_object, base_url):
    parsed_url = list(urlparse.urlparse(base_url))
    parsed_url[2] = pombola_object.get_absolute_url()
    return urlparse.urlunparse(parsed_url)

def add_extra_popolo_data_for_person(person, popolo_object, base_url):
    popolo_object['pa_url'] = make_pa_url(person, base_url)

    personinterests = person.interests_register_entries.all()
    if personinterests:
        interests = {}
        for entry in personinterests:
            release = entry.release
            category = entry.category
            interests.setdefault(release.name, {})
            interests[release.name].setdefault(category.name, [])

            #assuming no entrylineitems with duplicate keys within an entry
            entrylineitems = dict((e.key, e.value) for e in entry.line_items.all())

            interests[release.name][category.name].append(entrylineitems)

        popolo_object['interests_register'] = interests

def add_extra_popolo_data_for_organization(organisation, popolo_object, base_url):
    popolo_object['pa_url'] = make_pa_url(organisation, base_url)
    if organisation.kind.slug in ('constituency-office', 'constituency-area'):
        #assume constituency offices have only one linked location
        places = organisation.place_set.all()
        if places and places[0].location:
            popolo_object['lat'] = places[0].location.y
            popolo_object['lng'] = places[0].location.x
