import sys
from django.utils import dateparse
from rest_framework import status
from .models import Highlight, Note
from .serializers import HighlightSerializer, NoteSerializer

class DataSynchronizer:
    """Params:
    - client_highlights_version: datetime iso 8601 (string from request body)
    - client_notes_version: datetime iso 8601 (string from request body)
    - client_highlights: highlights (string from request body)
    - client_notes: notes (string from request body)
    - user: user obj from request
    """
    def __init__(self, client_highlights_version, client_notes_version, client_highlights, client_notes, user=None):
        self.client_highlights_version = client_highlights_version
        self.client_notes_version = client_notes_version
        self.client_highlights = client_highlights
        self.client_notes = client_notes
        self.user = user


    def _get_newer_highlights_notes_serializers(self):
        """Returns:
        - newer_highlights_serializer: HighlightSerializer instance
        - newer_notes_serializer: NoteSerializer instance
        """
        if self.client_highlights_version is not None:
            newer_highlights = Highlight.objects.filter(modified_at__gt=dateparse.parse_datetime(self.client_highlights_version), owner=self.user)
        else:
            newer_highlights = Highlight.objects.filter(owner=self.user)

        if self.client_notes_version is not None:
            newer_notes = Note.objects.filter(modified_at__gt=dateparse.parse_datetime(self.client_notes_version), owner=self.user)
        else:
            newer_notes = Note.objects.filter(owner=self.user)
        
        return HighlightSerializer(newer_highlights, many=True), NoteSerializer(newer_notes, many=True)


    def sync(self):
        """Returns:
        - dictionary containing data to be serialized
        - DRF's HTTP status
        - success status (bool)
        """
        try:
            # Save highlights and notes from the request (if any)...
            highlight_serializer = HighlightSerializer(data=self.client_highlights, many=True)
            notes_serializer = NoteSerializer(data=self.client_notes, many=True)
            if highlight_serializer.is_valid(raise_exception=True) and notes_serializer.is_valid(raise_exception=True):
                highlight_serializer.save(owner=self.user)
                notes_serializer.save(owner=self.user)

                server_highlights_version = Highlight.objects.filter(owner=self.user).first().modified_at if Highlight.objects.filter(owner=self.user).first() else self.client_highlights_version
                server_notes_version = Note.objects.filter(owner=self.user).first().modified_at if Note.objects.filter(owner=self.user).first() else self.client_notes_version

                newer_highlights_serializer, newer_notes_serializer = self._get_newer_highlights_notes_serializers()
                print('Begin sanity check for two new serializers...')
                print('Newer highlight serializer data: ', newer_highlights_serializer.data)
                print('Newer note serializer data: ', newer_notes_serializer.data)

                # ... and return newer highlights and notes (if any)
                return {
                    'highlights': newer_highlights_serializer.data,
                    'highlights_version': server_highlights_version,
                    'notes': newer_notes_serializer.data,
                    'notes_version': server_notes_version,
                }, status.HTTP_200_OK, True
        except:
            print(f'Error: {sys.exc_info()[1]}')
            return {'error': f"{sys.exc_info()[1]}"}, status.HTTP_500_INTERNAL_SERVER_ERROR, False
