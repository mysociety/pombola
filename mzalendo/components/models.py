import datetime
import json
import re

from popit import PopIt

from django.core.cache import cache


def parse_popit_date(s):
    return datetime.datetime.strptime(re.sub('T.*', '', s), '%Y-%m-%d').date()


class PartialDate(object):

    required_keys = ('start', 'end', 'formatted')
    range_ends = ('start', 'end')

    def __init__(self, partial_date_dictionary):
        if not all(x in partial_date_dictionary for x in PartialDate.required_keys):
            raise Exception, "The partial date dictionary must have all of %s, but it was: %s" % (str(PartialDate.required_keys), partial_date_dictionary)
        self.start = parse_popit_date(partial_date_dictionary['start'])
        self.end = parse_popit_date(partial_date_dictionary['end'])

    @classmethod
    def create(cls, partial_date_dictionary):
        if not all(x in partial_date_dictionary for x in PartialDate.required_keys):
            raise Exception, "The partial date dictionary must have all of %s, but it was: %s" % (str(PartialDate.required_keys), partial_date_dictionary)
        if any(partial_date_dictionary[x] is None for x in PartialDate.range_ends):
            return None
        else:
            return cls(partial_date_dictionary)

    def pretty_print(self):
        if self.start == self.end:
            # If the start and end are the same it's an exact date,
            # format it as YYYY-MM-DD:
            return str(self.start)
        else:
            # Lots of these dates will be from the first day of a
            # month to the last, or from the first day of the year to
            # the last - detect those cases and format them as YYYY-MM
            # or YYYY:
            if self.start.day == 1:
                next_day = self.end + datetime.timedelta(days=1)
                if next_day.day == 1:
                    # Then the partial data covers complete months.
                    # Check it it's from one next year's day to the
                    # next:
                    if (self.start.month == 1) and (next_day.month == 1) and (next_day.year == (self.start.year + 1)):
                        return str(self.start.year)
                    else:
                        start_months = self.start.year * 12 + (self.start.month - 1)
                        end_months = next_day.year * 12 + (next_day.month - 1)
                        if end_months == (start_months + 1):
                            return "%02d-%02d" % (self.start.year, self.start.month)
            return "%s to %s" % (self.start, self.end)

    def __str__(self):
        return self.pretty_print()


class PopItBase(object):

    def __init__(self, client, dictionary):
        self.client = client
        self.popit_id = dictionary[client.id_key]
        if 'name' in dictionary:
            self.name = dictionary['name']
        if 'title' in dictionary:
            self.title = dictionary['title']
        if 'slug' in dictionary:
            self.slug = dictionary['slug']
        self.api_url = dictionary['meta']['api_url']
        self.edit_url = dictionary['meta']['edit_url']    
        self.completed = False

    def complete_from_api(self):
        slumber_resource = getattr(self.client.popit, self.resource_name)
        result_dict = slumber_resource(self.popit_id).get()
        if 'error' in result_dict:
            raise Exception, "Error fetching %s: %s" % (self.resource_name, result_dict['error'])
        if self.complete_from_api_specific(result_dict['result']):
            self.completed = True


class PopItPerson(PopItBase):

    def __init__(self, client, dictionary):
        self.resource_name = "person"
        self.positions = {}
        self.date_of_birth = None
        self.date_of_death = None
        self.images = None
        self.contact_details = None
        self.other_names = None
        super(PopItPerson,self).__init__(client, dictionary)
        if client.api_version != "v1":
            self.complete_from_api_specific(dictionary)

    def complete_from_api_specific(self, result_dict):
        self.date_of_birth = PartialDate.create(result_dict['personal_details']['date_of_birth'])
        self.date_of_death = PartialDate.create(result_dict['personal_details']['date_of_death'])
        self.images = result_dict['images']
        self.links = result_dict['links']
        self.contact_details = result_dict['contact_details']
        self.other_names = result_dict['other_names']
        return True

    def __unicode__(self):
        return u"<Person: %s [%s]>" % (self.name, self.popit_id)

    def get_positions(self):
        return self.positions.values()

    def add_position(self, position):
        self.positions[position.popit_id] = position


class PopItPosition(PopItBase):

    def __init__(self, client, dictionary):
        self.resource_name = "position"
        super(PopItPosition,self).__init__(client, dictionary)
        self.start_date = None
        self.end_date = None
        self.person = None
        self.organisation = None
        if client.api_version != "v1":
            self.complete_from_api_specific(dictionary)

    def complete_from_api_specific(self, result_dict):
        if ('start_date' not in result_dict) or ('end_date' not in result_dict):
            raise Exception, "start_date or end_date was missing from %s" % (result_dict)
        self.start_date = PartialDate.create(result_dict['start_date'])
        self.end_date = PartialDate.create(result_dict['end_date'])
        self.person = self.client.all_people[result_dict['person']]
        self.person.add_position(self)
        self.organisation = self.client.all_organisations[result_dict['organisation']]
        self.organisation.add_position(self)
        return True

    def active_on_date(self, date_to_test):
        # If the start_date is defined, but the end_date is None, that
        # means the position is still active as far as we know:
        if self.start_date and (self.end_date is None):
            return date_to_test >= self.start_date.start
        # If both are defined, just check it's in the range:
        elif self.start_date and self.end_date:
            return (date_to_test >= self.start_date.start) and (date_to_test <= self.end_date.end)
        else:
            raise Exception, "We don't know how to handle start_date: %s and end_date: %s" % (self.start_date, self.end_date)

    def current(self):
        return self.active_on_date(datetime.date.today())

    def __unicode__(self):
        return u"<Position: %s [%s] (%s to %s)>" % (self.title, self.popit_id, self.start_date, self.end_date)


class PopItOrganisation(PopItBase):

    def __init__(self, client, dictionary):
        self.resource_name = "organisation"
        self.positions = {}
        self.images = None
        self.category = None
        super(PopItOrganisation,self).__init__(client, dictionary)
        if client.api_version != "v1":
            self.complete_from_api_specific(dictionary)

    def complete_from_api_specific(self, result_dict):
        self.images = result_dict['images']
        self.category = result_dict['category']
        return True

    def __unicode__(self):
        return u"<Organisation: %s [%s]>" % (self.name, self.popit_id)

    def get_positions(self):
        return self.positions.values()

    def add_position(self, position):
        self.positions[position.popit_id] = position


class NoSuchPopItObject(Exception):
    pass


class MultiplePopItObjects(Exception):
    pass


class ComponentClient(object):

    def __init__(self, popit_instance=None):
        if popit_instance is None:
            self.popit = PopIt(instance='kenyan-politicians',
                               hostname='popit.mysociety.org',
                               user='mark-kenya@longair.net',
                               password='9ckY2bYi')
        else:
            self.popit = popit_instance
        self.all_people = {}
        self.all_positions = {}
        self.all_organisations = {}
        self.id_key = "_id" if popit_instance.api_version == "v1" else "id"

    @property
    def api_version(self):
        return self.popit.api_version

    @staticmethod
    def get_cached_client(component_client_key):
        cached_client = cache.get(component_client_key)
        if not cached_client:
            cached_client = ComponentClient()
            cached_client.setup()
        return cached_client

    def setup(self):

        # Fetch organisations and people before positions (which will
        # store references to organisations and people).

        all_organisations = self.popit.organisation.get()
        if 'errors' in all_organisations:
            raise Exception, "Error on fetching all organisations: " + str(all_organisations['errors'])

        for organisation_dictionary in all_organisations['results']:
            o = PopItOrganisation(self, organisation_dictionary)
            self.all_organisations[o.popit_id] = o

        all_people = self.popit.person.get()
        if 'errors' in all_people:
            raise Exception, "Error on fetching all people: " + str(all_people['errors'])

        for person_dictionary in all_people['results']:
            p = PopItPerson(self, person_dictionary)
            self.all_people[p.popit_id] = p

        all_positions = self.popit.position.get()
        if 'errors' in all_positions:
            raise Exception, "Error on fetching all positions: " + str(all_positions['errors'])

        # With v1 of the API the positions fetched won't have the
        # references to the person and organisation that it links, so
        # call complete_from_api on each:

        for position_dictionary in all_positions['results']:
            p = PopItPosition(self, position_dictionary)
            if self.api_version == "v1":
                p.complete_from_api()
            self.all_positions[p.popit_id] = p

    def get_all_people(self):
        return self.all_people.values()

    def get_person(self, person_id):
        return self.all_people.get(person_id, None)

    def get_position(self, position_id):
        return self.all_positions.get(position_id, None)

    def _get(self, popit_dictionary, **kwargs):
        # This is very general, but inefficient - for example, if
        # lookups by name are common, we should build a dictionary
        # mapping name to object:
        matches = [o for o in popit_dictionary.values()
                   if all(getattr(o, k) == kwargs[k] for k in kwargs)]
        if len(matches) == 0:
            raise NoSuchPopItObject
        elif len(matches) > 1:
            raise MultiplePopItObjects
        else:
            return matches[0]

    def _filter(self, popit_dictionary, **kwargs):
        return [o for o in popit_dictionary.values()
                if all(getattr(o, k) == kwargs[k] for k in kwargs)]

    def get_organisation_by_name(self, name):
        return self._get(self.all_organisations, name=name)

    def get_person_by_name(self, name):
        return self._get(self.all_people, name=name)

    def filter_positions_by_title(self, title):
        return self._filter(self.all_positions, title=title)

    def filter_current_postitions_in_organisation(self, organisation):
        today = datetime.date.today()
        return [o for o in self._filter(self.all_positions, organisation=organisation)
                if o.active_on_date(today)]
