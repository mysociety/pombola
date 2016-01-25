from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.response import Response

from ..models import Entry, Sitting, Source, Venue
from .serializers import (
    EntrySerializer, SittingSerializer, SittingWithEntriesSerializer,
    SourceSerializer, VenueSerializer
)


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.order_by('id')
    serializer_class = EntrySerializer


class SittingViewSet(viewsets.GenericViewSet):

    queryset = Entry.objects.order_by('id')

    def list(self, request, version=None):
        queryset = Sitting.objects.order_by('id') \
            .select_related('source', 'venue')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SittingSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SittingSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    def retrieve(self, request, pk=None, version=None):
        prefetch_qs = Entry.objects.select_related('speaker')
        queryset = Sitting.objects.order_by('id') \
            .select_related('source', 'venue') \
            .prefetch_related(Prefetch('entry_set', queryset=prefetch_qs))
        sitting = get_object_or_404(queryset, pk=pk)
        serializer = SittingWithEntriesSerializer(
            sitting, context={'request': request}
        )
        return Response(serializer.data)

class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.order_by('id')
    serializer_class = SourceSerializer


class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.order_by('id')
    serializer_class = VenueSerializer
