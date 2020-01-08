from .models import User, Device, Highlight, Note
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        # 'password' management is handled by an endpoint
        #fields = ['url', 'id', 'email', 'full_name', 'phone', 'devices', 'highlights', 'notes']
        fields = ['url', 'id', 'email', 'full_name', 'phone']


class DeviceSerializer(serializers.ModelSerializer):
    #owner = serializers.ReadOnlyField(source='owner.id')
    
    class Meta:
        model = Device
        fields = ['id', 'client_version', 'os', 'fcm_token']


class HighlightSerializer(serializers.ModelSerializer):
    #owner = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = Highlight
        fields = ['uid', 'key', 'verse', 'color', 'created_at', 'modified_at']

    def create(self, validated_data):
        try:
            key = validated_data.get('key', None)
            owner = validated_data.get('owner', None)
            highlight = Highlight.objects.get(key=key, owner=owner)
            # Update the object only if input is newer
            if highlight.modified_at <= validated_data.get('modified_at', None):
                highlight.verse = validated_data.get('verse', None)
                highlight.color = validated_data.get('color', None)
                highlight.modified_at = validated_data.get('modified_at', None)
                highlight.save()
        except Highlight.DoesNotExist:
            highlight = Highlight.objects.create(**validated_data)
        return highlight


class NoteSerializer(serializers.ModelSerializer):
    #owner = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = Note
        fields = ['uid', 'title', 'body', 'key', 'created_at', 'modified_at']

    def create(self, validated_data):
        try:
            uid = validated_data.get('uid', None)
            created_at = validated_data.get('created_at', None)
            owner = validated_data.get('owner', None)
            note = Note.objects.get(uid=uid, created_at=created_at, owner=owner)
            # Update the object only if input is newer
            if note.modified_at <= validated_data.get('modified_at', None):
                note.title = validated_data.get('title', None)
                note.body = validated_data.get('body', None)
                note.key = validated_data.get('key', None) # this should be the same
                note.modified_at = validated_data.get('modified_at', None)
                note.save()
        except Note.DoesNotExist:
            note = Note.objects.create(**validated_data)
        return note
