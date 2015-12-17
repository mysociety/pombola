from django.core.management.base import NoArgsCommand

from pombola.core.models import ParliamentarySession, Person


class Command(NoArgsCommand):

    help = "Go through people who are MP aspirants, and check that they're associated with a 2013 constituency"

    def handle_noargs(self, **options):
        next_session = ParliamentarySession.objects.get(slug="na2013")
        for person in Person.objects.all():
            if not person.is_aspirant():
                continue
            aspirant_mp_positions = [ap for ap in person.aspirant_positions() if ap.title.slug == 'aspirant-mp']
            if not aspirant_mp_positions:
                continue
            print person
            if len(aspirant_mp_positions) > 1:
                print "  Warning: more than one Aspirant MP position:"
                for amp in aspirant_mp_positions:
                    print "    ", amp
                continue
            amp = aspirant_mp_positions[0]
            if amp.place.parliamentary_session != next_session:
                print """  Warning: the place associated with this Aspirant MP position
  %s - %s
  is for the wrong parliamentary session.  It should be a
  place associated with the parliamentary session: %s""" % (amp.place,
                                                            amp.place.parliamentary_session,
                                                            next_session)
