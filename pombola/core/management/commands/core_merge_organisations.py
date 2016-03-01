# This admin command is to save having to do a series of manual steps
# when merging to people in Pombola.

import pombola.core.models as core_models

from ..merge import MergeCommandBase


class Command(MergeCommandBase):
    admin_url_name = 'admin:core_organisation_change'
    basic_fields_to_check = (
        'started',
        'ended',
        'kind',
        'summary',
    )
    model_class = core_models.Organisation

    def model_specific_merge(self, to_keep, to_delete, **options):
        core_models.Position.objects.filter(organisation=to_delete) \
            .update(organisation=to_keep)
        core_models.Place.objects.filter(organisation=to_delete) \
            .update(organisation=to_keep)
        core_models.OrganisationRelationship.objects \
            .filter(organisation_a=to_delete) \
            .update(organisation_a=to_keep)
        core_models.OrganisationRelationship.objects \
            .filter(organisation_b=to_delete) \
            .update(organisation_b=to_keep)
        core_models.ParliamentarySession.objects \
            .filter(house=to_delete) \
            .update(house=to_keep)
