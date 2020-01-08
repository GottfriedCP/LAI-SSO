import datetime, random, sys
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
#from django.utils import timezone
from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from .models import User, Device, Highlight, Note
from .serializers import UserSerializer, DeviceSerializer, HighlightSerializer, NoteSerializer
from .synchronizer import DataSynchronizer


def dummy(request):
    return HttpResponse('Indonesian Bible Society')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request, format=None):
    """Register a new user."""
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')
        full_name = request.data.get('full_name')
        phone = request.data.get('phone')
        if email is None or password is None or full_name is None or phone is None:
            return Response({'error': "nama, nomor telepon, email, dan kata sandi harus diisi."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(email=email, password=password, full_name=full_name, phone=phone)
        except IntegrityError:
            return Response({'error': 'email atau nomor telepon sudah terdaftar.'}, status=status.HTTP_400_BAD_REQUEST)
        print(f'New user created: {user}')
        # Create auth (bearer) token
        token = Token.objects.create(user=user)
        # Proceed to login
        login(request, user)
        # Send welcome email to that user
        subject = 'Verifikasi Akun'
        from_email = '"Alkitab Digital LAI" <no-reply@alkitab.or.id>'
        to = user.email
        verify_url = f"{request.get_host()}{reverse('verify-account')}?code={user.verification_code}/"
        text_content = f"""Selamat datang di Alkitab Digital LAI.

        Mohon segera melakukan verifikasi akun di tautan berikut:

        {verify_url}

        Email ini dikirim oleh mesin; mohon untuk tidak membalas email ini.

        Indonesian Bible Society"""
        html_content = render_to_string('apiv1/welcome_mail.html', {
            'verify_url': verify_url,
            })
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, 'text/html')
        # Finish creating email body and send the email
        msg.send()

        return Response({
            'id': user.id,
            'email': email,
            'full_name': full_name,
            'phone': phone,
            'token': token.key,
            }, status=status.HTTP_201_CREATED)


def verify_account(request):
    verification_code = request.GET.get('code', '0')
    if User.objects.filter(verification_code=verification_code).exists():
        User.objects.filter(verification_code=verification_code).update(is_verified=True, verification_code=None)
        status = 'Akun telah berhasil diverifikasi. Anda boleh menutup jendela ini.'
        return render(request, 'apiv1/verification_status.html', {'status': status})
        
    status = 'Tautan sudah tidak berlaku atau kode verifikasi tidak valid.'
    return render(request, 'apiv1/verification_status.html', {'status': status})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_verification_code(request, format=None):
    """Currently unused."""
    if request.method == 'GET':
        email = request.GET.get('email')
        verification_code = str(random.randint(1000, 9999))
        
        try:
            # Send the verification code to the user.
            subject = 'Verification Code'
            from_email = '"Alkitab Digital LAI" <no-reply@alkitab.or.id>'
            to = str(email).strip()
            text_content = f"""Kode verifikasi: {verification_code}

            Email ini dikirim oleh mesin; mohon untuk tidak membalas email ini.

            Indonesian Bible Society"""
            html_content = render_to_string('apiv1/verification_code.html', {
                'verification_code': verification_code,
                })
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, 'text/html')
            # Finish creating email body and send the email.
            msg.send()

            return Response({'verification_code': verification_code})
        except:
            print(f'Error: {sys.exc_info()[1]}')
            return Response({'error': f"{sys.exc_info()[1]}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request, format=None):
    """Log a user in."""
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')
        if email is None or password is None:
            return Response({'error': "mohon isi email dan kata sandi."}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, email=email, password=password)
        # Log the user in
        if user is not None:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)

            server_highlights_version = Highlight.objects.filter(owner=user).first().modified_at if Highlight.objects.filter(owner=user).first() else "1970-01-01T00:00:00Z"
            server_notes_version = Note.objects.filter(owner=user).first().modified_at if Note.objects.filter(owner=user).first() else "1970-01-01T00:00:00Z"

            return Response({
                'id': user.id, 
                'email': user.email, 
                'full_name': user.full_name, 
                'phone': user.phone, 
                'token': token.key,

                'highlights': HighlightSerializer(Highlight.objects.filter(color__isnull=False, owner=user), many=True).data,
                'highlights_version': server_highlights_version,
                'notes': NoteSerializer(Note.objects.filter(key__isnull=False, owner=user), many=True).data,
                'notes_version': server_notes_version,
                }, status=status.HTTP_200_OK)
        return Response({'error': "email atau kata sandi salah."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request, format=None):
    """Log a user out. Can be ignored as this RESTApi doesn't use session."""
    if request.method == 'POST':
        logout(request)
        return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def profile_change(request, format=None):
    """Update an existing user's full name, email, and phone number."""
    if request.method == 'PUT':
        email = request.data.get('email')
        full_name = request.data.get('full_name')
        phone = request.data.get('phone')
        if email is None or full_name is None or phone is None:
            return Response({'error': "mohon isi nama, email, dan nomor telepon."}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        try:
            user.email = email
            user.full_name = full_name
            user.phone = phone
            user.save()
        except:
            print(f'Error: {sys.exc_info()[1]}')
            return Response({'error': f"{sys.exc_info()[1]}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'id': user.id, 'email': user.email, 'full_name': user.full_name, 'phone': user.phone}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def password_change(request, format=None):
    """Change a user's password. Requires old password and new one."""
    if request.method == 'POST':
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if old_password is None or new_password is None:
            return Response({'error': "mohon isi kata sandi saat ini dan kata sandi baru."}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, email=request.user.email, password=old_password)
        if user is not None:
            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_200_OK)
        return Response({'error': "kata sandi saat ini tidak valid."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset(request, format=None):
    """Reset a user's password internally and notify the user."""
    if request.method == 'POST':
        email = request.data.get('email')
        if email is None:
            return Response({'error': "mohon isi email."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
            new_password = str(random.randint(100000, 999999))
            user.set_password(new_password)

            # Notify the user
            subject = 'Password Reset'
            from_email = '"Alkitab Digital LAI" <no-reply@alkitab.or.id>'
            to = user.email
            text_content = f"""Shalom {user.full_name},

            Kami menerima permintaan reset password Anda. Berikut password Anda yang baru:

            Email: {user.email}
            Password: {new_password}

            Email ini dikirim oleh mesin; mohon untuk tidak membalas email ini.

            Indonesian Bible Society"""
            html_content = render_to_string('apiv1/password_reset.html', {
                'new_password': new_password,
                'full_name': user.full_name,
                'email_address': user.email,
                })
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, 'text/html')
            # Finish creating email body and send the email
            msg.send()
            user.save()
        except User.DoesNotExist:
            return Response({'error': "email tidak ada di sistem kami."}, status=status.HTTP_404_NOT_FOUND)
        except:
            print(f'Error: {sys.exc_info()[1]}')
            return Response({'error': f"{sys.exc_info()[1]}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def user_list(request, format=None):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def user_detail(request, pk, format=None):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': "user not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def init_app(request, format=None):
    """This will be called on app startup.
    """
    if request.method == 'POST':
        # years_ago = timezone.now() - datetime.timedelta(days=365*5)
        # if request.user.auth_token.created < years_ago:
        #     old_token, _ = Token.objects.get_or_create(user=request.user)
        #     old_token.delete()
        #     token = Token.objects.get_or_create(user=request.user)
        #     return Response({'error': "token no longer valid"}, status=status.HTTP_401_UNAUTHORIZED)
        
        resp = {
            'id': request.user.id, 
            'email': request.user.email, 
            'full_name': request.user.full_name, 
            'phone': request.user.phone
            }

        client_highlights_version = request.data.get('highlights_version', "1970-01-01T00:00:00Z")
        client_notes_version = request.data.get('notes_version', "1970-01-01T00:00:00Z")
        client_highlights = request.data.get('highlights', [])
        client_notes = request.data.get('notes', [])
        
        sync_data, sync_status, is_success = DataSynchronizer(client_highlights_version, client_notes_version, client_highlights, client_notes, user=request.user).sync()

        resp.update(sync_data)

        return Response(resp, status=sync_status)
        

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def device_list(request, format=None):
    """Submit a user's device (and FCM token) or get the list of devices."""
    if request.method == 'GET':
        devices = Device.objects.filter(owner=request.user)
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = DeviceSerializer(data=request.data)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save(owner=request.user)
        except ValidationError:
            print(f'Error saving device object: {serializer.errors}')
        except:
            return Response({'error': f"{sys.exc_info()[1]}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_cloud(request, format=None):
    """Synchronize data between client and server.
    Server will store or update all objects submitted by client,
    and return objects (if any) previously unknown to the client.
    """
    if request.method == 'POST':
        client_highlights_version = request.data.get('highlights_version', "1970-01-01T00:00:00Z")
        client_notes_version = request.data.get('notes_version', "1970-01-01T00:00:00Z")
        client_highlights = request.data.get('highlights')
        client_notes = request.data.get('notes')
        
        data, status, is_success = DataSynchronizer(client_highlights_version, client_notes_version, client_highlights, client_notes, user=request.user).sync()
        return Response(data, status=status)
