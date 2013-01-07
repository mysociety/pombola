# These are the classes for API v1

class FakePersonResource(object):

    def __call__(self, person_id):
        self.person_id = person_id
        return self

    def __init__(self):
        self.person_id = None

    def get(self):
        if self.person_id is None:
            return {
                'results': [
                    {"_id": "50c60af171ec32dd6e00110f",
                     "name": "Magerer Kiprono Langat",
                     "slug": "magerer-kiprono-langat",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/person//50c60af171ec32dd6e00110f",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/magerer-kiprono-langat"
                            }
                     },
                    {"_id": "50c60bdc71ec32dd6e001713",
                     "name": "Sally Jepngetich Kosgei",
                     "slug": "sally-jepngetich-kosgei",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/person//50c60bdc71ec32dd6e001713",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/sally-jepngetich-kosgei"
                            }
                     },
                    {"_id": "50c60a0e71ec32dd6e0009d3",
                     "name": "Edwin Ochieng Yinda",
                     "slug": "edwin-ochieng-yinda",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/person//50c60a0e71ec32dd6e0009d3",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/edwin-ochieng-yinda"
                            }
                     },
                    ]
                }
        elif self.person_id == "50c60af171ec32dd6e00110f":
            return {
                'result': {
                    "__v": 1,
                    "_id": "50c60af171ec32dd6e00110f",
                    "name": "Magerer Kiprono Langat",
                    "slug": "magerer-kiprono-langat",
                    "personal_details": {
                        "date_of_death": {
                            "formatted": "",
                            "end": None,
                            "start": None
                            },
                        "date_of_birth": {
                            "formatted": "Jan 1 - Dec 31, 1973",
                            "end": "1973-12-31T00:00:00.000Z",
                            "start": "1973-01-01T00:00:00.000Z"
                            }
                        },
                    "_internal": {
                        "name_words": [
                            "magerer",
                            "kiprono",
                            "langat"
                            ],
                        "name_dm": [
                            "MKRR",
                            "MJRR",
                            "KPRN",
                            "KPRN",
                            "LNKT",
                            "LNKT",
                            "magerer",
                            "kiprono",
                            "langat"
                            ]
                        },
                    "images": [
                        {
                            "url": "http://info.mzalendo.com/media_root/images/magerer_kiprono_langat.png",
                            "_id": "50c60af171ec32dd6e001110",
                            "created": "2012-12-10T16:16:49.729Z",
                            "meta": {
                                "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/person/50c60af171ec32dd6e00110f/50c60af171ec32dd6e00110f/images/50c60af171ec32dd6e001110",
                                "image_url": "http://info.mzalendo.com/media_root/images/magerer_kiprono_langat.png",
                                "can_use_image_proxy": False
                                }
                            }
                        ],
                    "links": [ ],
                    "contact_details": [ ],
                    "other_names": [ ],
                    "meta": {
                        "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/magerer-kiprono-langat",
                        "positions_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/position?person=50c60af171ec32dd6e00110f"
                        }
                    }
                }
        else:
            raise Exception, "Unknown person..."

class FakeOrganisationResource(object):

    def __call__(self, organisation_id):
        self.organisation_id = organisation_id
        return self

    def __init__(self):
        self.organisation_id = None

    def get(self):
        if self.organisation_id is None:
            return {'results': [
                    {"name": "Parliament",
                     "slug": "parliament",
                     "_id": "50c6093771ec32dd6e000453",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/organisation//50c6093771ec32dd6e000453",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/organisation/parliament"
                            }},
                    ]}
        elif self.organisation_id == "50c6093771ec32dd6e000453":
            return {"result": {
                    "category": "political",
                    "name": "Parliament",
                    "slug": "parliament",
                    "_id": "50c6093771ec32dd6e000453",
                    "__v": 0,
                    "images": [ ],
                    "meta": {
                        "edit_url": "http://kenyan-politicians.popit.mysociety.org/organisation/parliament",
                        "positions_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/position?organisation=50c6093771ec32dd6e000453"
                        }}}
        else:
            raise Exception, "Unknown organisation_id: " + str(organisation_id)

class FakePositionResource(object):

    def __call__(self, position_id):
        self.position_id = position_id
        return self

    def __init__(self, position_id=None):
        self.position_id = None

    def get(self):
        if self.position_id is None:
            return {
                'results': [
                    {"person": "50c60af171ec32dd6e00110f",
                     "organisation": "50c6093771ec32dd6e000453",
                     "title": "Member of Parliament",
                     "_id": "50c60af271ec32dd6e001116",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/position//50c60af271ec32dd6e001116",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/position/50c60af271ec32dd6e001116"
                            }},
                    ]}
        elif self.position_id == "50c60af271ec32dd6e001116":
            return {'result': {
                    "person": "50c60af171ec32dd6e00110f",
                    "organisation": "50c6093771ec32dd6e000453",
                    "title": "Member of Parliament",
                    "_id": "50c60af271ec32dd6e001116",
                    "__v": 0,
                    "end_date": {
                        "formatted": "Mar 4, 2013",
                        "end": "2013-03-04T00:00:00.000Z",
                        "start": "2013-03-04T00:00:00.000Z"
                        },
                    "start_date": {
                        "formatted": "Jan 1 - Dec 31, 2008",
                        "end": "2008-12-31T00:00:00.000Z",
                        "start": "2008-01-01T00:00:00.000Z"
                        },
                    "meta": {
                        "edit_url": "http://kenyan-politicians.popit.mysociety.org/position/50c60af271ec32dd6e001116",
                        "person_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/person/50c60af171ec32dd6e00110f",
                        "organisation_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v1/organisation/50c6093771ec32dd6e000453"
                        }}}
        else:
            raise Exception, "Unknown position_id: " + str(self.position_id)

# These are the classes for API v0.1

class FakeCompletePersonResource(object):

    def __call__(self, person_id):
        self.person_id = person_id
        return self

    def __init__(self):
        self.person_id = None

    def get(self):
        if self.person_id is None:
            return {
                "results": [
                    {"name": "Sally Jepngetich Kosgei",
                     "slug": "sally-jepngetich-kosgei",
                     "personal_details": {
                            "date_of_death": {
                                "formatted": "",
                                "end": None,
                                "start": None
                                },
                            "date_of_birth": {
                                "formatted": "Jan 1 - Dec 31, 1949",
                                "end": "1949-12-31T00:00:00.000Z",
                                "start": "1949-01-01T00:00:00.000Z"
                                }
                            },
                     "images": [
                            {
                                "url": "http://info.mzalendo.com/media_root/images/sally_kosgei.jpg",
                                "_id": "50c60bdc71ec32dd6e001714",
                                "created": "2012-12-10T16:20:44.228Z"
                                }
                            ],
                     "links": [ ],
                     "contact_details": [ ],
                     "other_names": [ ],
                     "id": "50c60bdc71ec32dd6e001713",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/person//50c60bdc71ec32dd6e001713",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/sally-jepngetich-kosgei"
                            }
                     },
                    {"name": "Magerer Kiprono Langat",
                     "slug": "magerer-kiprono-langat",
                     "personal_details": {
                            "date_of_death": {
                                "formatted": "",
                                "end": None,
                                "start": None
                                },
                            "date_of_birth": {
                                "formatted": "Jan 1 - Dec 31, 1973",
                                "end": "1973-12-31T00:00:00.000Z",
                                "start": "1973-01-01T00:00:00.000Z"
                                }
                            },
                     "images": [
                            {
                                "url": "http://info.mzalendo.com/media_root/images/magerer_kiprono_langat.png",
                                "_id": "50c60af171ec32dd6e001110",
                                "created": "2012-12-10T16:16:49.729Z"
                                }
                            ],
                     "links": [ ],
                     "contact_details": [ ],
                     "other_names": [ ],
                     "id": "50c60af171ec32dd6e00110f",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/person//50c60af171ec32dd6e00110f",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/magerer-kiprono-langat"
                            }
                     },
                    {"name": "Edwin Ochieng Yinda",
                     "slug": "edwin-ochieng-yinda",
                     "personal_details": {
                            "date_of_death": {
                                "formatted": "",
                                "end": None,
                                "start": None
                                },
                            "date_of_birth": {
                                "formatted": "Jan 1 - Dec 31, 1951",
                                "end": "1951-12-31T00:00:00.000Z",
                                "start": "1951-01-01T00:00:00.000Z"
                                }
                            },
                     "images": [
                            {
                                "url": "http://info.mzalendo.com/media_root/images/Edwin_Yinda.png",
                                "_id": "50c60a0e71ec32dd6e0009d4",
                                "created": "2012-12-10T16:13:02.846Z"
                                }
                            ],
                     "links": [ ],
                     "contact_details": [ ],
                     "other_names": [ ],
                     "id": "50c60a0e71ec32dd6e0009d3",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/person//50c60a0e71ec32dd6e0009d3",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/edwin-ochieng-yinda"
                            }},
                    ]}
        elif self.person_id == "50c60af171ec32dd6e00110f":
            return {
                "result": {
                    "name": "Magerer Kiprono Langat",
                    "slug": "magerer-kiprono-langat",
                    "personal_details": {
                        "date_of_death": {
                            "formatted": "",
                            "end": None,
                            "start": None
                            },
                        "date_of_birth": {
                            "formatted": "Jan 1 - Dec 31, 1973",
                            "end": "1973-12-31T00:00:00.000Z",
                            "start": "1973-01-01T00:00:00.000Z"
                            }
                        },
                    "images": [
                        {
                            "url": "http://info.mzalendo.com/media_root/images/magerer_kiprono_langat.png",
                            "_id": "50c60af171ec32dd6e001110",
                            "created": "2012-12-10T16:16:49.729Z",
                            "meta": {
                                "image_url": "http://info.mzalendo.com/media_root/images/magerer_kiprono_langat.png",
                                "can_use_image_proxy": False
                                }
                            }
                        ],
                    "links": [ ],
                    "contact_details": [ ],
                    "other_names": [ ],
                    "id": "50c60af171ec32dd6e00110f",
                    "meta": {
                        "edit_url": "http://kenyan-politicians.popit.mysociety.org/person/magerer-kiprono-langat",
                        "positions_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/position?person=50c60af171ec32dd6e00110f"
                        }}}
        else:
            raise Exception, "Unknown person..."

class FakeCompleteOrganisationResource(object):

    def __call__(self, organisation_id):
        self.organisation_id = organisation_id
        return self

    def __init__(self):
        self.organisation_id = None

    def get(self):
        if self.organisation_id is None:
            return {
                "results": [
                    {"category": "political",
                     "name": "Parliament",
                     "slug": "parliament",
                     "images": [ ],
                     "id": "50c6093771ec32dd6e000453",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/organisation//50c6093771ec32dd6e000453",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/organisation/parliament"
                            }},
                    ]}
        elif self.organisation_id == "50c6093771ec32dd6e000453":
            return {
                "result": {
                    "category": "political",
                    "name": "Parliament",
                    "slug": "parliament",
                    "images": [ ],
                    "id": "50c6093771ec32dd6e000453",
                    "meta": {
                        "edit_url": "http://kenyan-politicians.popit.mysociety.org/organisation/parliament",
                        "positions_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/position?organisation=50c6093771ec32dd6e000453"
                        }}}
        else:
            raise Exception, "Unknown organisation_id: " + str(organisation_id)

class FakeCompletePositionResource(object):

    def __call__(self, position_id):
        self.position_id = position_id
        return self

    def __init__(self, position_id=None):
        self.position_id = None

    def get(self):
        if self.position_id is None:
            return {
                'results': [
                    {"person": "50c60af171ec32dd6e00110f",
                     "organisation": "50c6093771ec32dd6e000453",
                     "title": "Member of Parliament",
                     "end_date": {
                            "formatted": "Mar 4, 2013",
                            "end": "2013-03-04T00:00:00.000Z",
                            "start": "2013-03-04T00:00:00.000Z"
                            },
                     "start_date": {
                            "formatted": "Jan 1 - Dec 31, 2008",
                            "end": "2008-12-31T00:00:00.000Z",
                            "start": "2008-01-01T00:00:00.000Z"
                            },
                     "id": "50c60af271ec32dd6e001116",
                     "meta": {
                            "api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/position//50c60af271ec32dd6e001116",
                            "edit_url": "http://kenyan-politicians.popit.mysociety.org/position/50c60af271ec32dd6e001116"
                            }},
                    ]}
        elif self.position_id == "50c60af271ec32dd6e001116":
            return {
                "result": {
                    "person": "50c60af171ec32dd6e00110f",
                    "organisation": "50c6093771ec32dd6e000453",
                    "title": "Member of Parliament",
                    "end_date": {
                        "formatted": "Mar 4, 2013",
                        "end": "2013-03-04T00:00:00.000Z",
                        "start": "2013-03-04T00:00:00.000Z"
                        },
                    "start_date": {
                        "formatted": "Jan 1 - Dec 31, 2008",
                        "end": "2008-12-31T00:00:00.000Z",
                        "start": "2008-01-01T00:00:00.000Z"
                        },
                    "id": "50c60af271ec32dd6e001116",
                    "meta": {
                        "edit_url": "http://kenyan-politicians.popit.mysociety.org/position/50c60af271ec32dd6e001116",
                        "person_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/person/50c60af171ec32dd6e00110f",
                        "organisation_api_url": "http://kenyan-politicians.popit.mysociety.org/api/v0.1/organisation/50c6093771ec32dd6e000453"
                        }}}
        else:
            raise Exception, "Unknown position_id: " + str(self.position_id)


class FakePopIt(object):

    def __init__(self, api_version="v1"):
        self._api_version = api_version

    @property
    def api_version(self):
        return self._api_version

    @property
    def organisation(self):
        if self._api_version == "v1":
            return FakeOrganisationResource()
        elif self._api_version == "v0.1":
            return FakeCompleteOrganisationResource()
        else:
            raise Exception, "Unknown API version %s" % (self._api_version,)

    @property
    def person(self):
        if self._api_version == "v1":
            return FakePersonResource()
        elif self._api_version == "v0.1":
            return FakeCompletePersonResource()
        else:
            raise Exception, "Unknown API version %s" % (self._api_version,)

    @property
    def position(self):
        if self._api_version == "v1":
            return FakePositionResource()
        elif self._api_version == "v0.1":
            return FakeCompletePositionResource()
        else:
            raise Exception, "Unknown API version %s" % (self._api_version,)
