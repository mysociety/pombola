from rest_framework import serializers

from pombola.core.models import Person
from ..models import Entry, Sitting, Source, Venue


class InlinePersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ('id', 'legal_name', 'slug')


class EntrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Entry
        order_by = 'text_counter'
        fields = (
            'id', 'url',
            'text_counter',
            'type', 'speaker_name', 'speaker_title', 'speaker',
            'content',
        )
    speaker = InlinePersonSerializer(read_only=True)


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = (
            'name', 'date', 'url', 'list_page',
            'last_processing_attempt', 'last_processing_success'
        )


class SittingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sitting
        fields = (
            'id', 'url', 'source', 'venue',
            'start_date', 'start_time',
            'end_date', 'end_time',
        )
    source = SourceSerializer(read_only=True)


class SittingWithEntriesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sitting
        fields = (
            'id', 'url', 'source', 'venue',
            'start_date', 'start_time',
            'end_date', 'end_time',
            'entries',
        )
    source = SourceSerializer(read_only=True)
    entries = EntrySerializer(many=True, read_only=True, source='entry_set')


class VenueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Venue
        fields = ('id', 'url', 'name', 'slug')
