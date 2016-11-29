from pombola.search.views import SearchBaseView

from haystack.query import SQ

from speeches.models import Speech


class SASearchView(SearchBaseView):
    def __init__(self, *args, **kwargs):
        super(SASearchView, self).__init__(*args, **kwargs)

        del self.search_sections['speeches']

        self.search_sections['questions'] = {
            'model': Speech,
            'title': 'Questions and Answers',
            'filter': {
                'args': [SQ(tags='question') | SQ(tags='answer')],
            }
        }

        self.search_sections['committee'] = {
            'model': Speech,
            'title': 'Committee Appearance',
            'filter': {
                'kwargs': {
                    'tags': 'committee'
                }
            }
        }

        self.search_sections['hansard'] = {
            'model': Speech,
            'title': 'Hansard',
            'filter': {
                'kwargs': {
                    'tags': 'hansard'
                }
            }
        }

        self.section_ordering.remove('speeches')

        self.section_ordering += [
            'questions', 'committee', 'hansard'
        ]
