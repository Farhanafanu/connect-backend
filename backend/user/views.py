
from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status,viewsets
from user.models import *
from .serializer import *
from rest_framework.permissions import AllowAny
from .email import send_otp_email
import jwt, datetime
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.parsers import JSONParser
from django.core.exceptions import ValidationError
from django.db.models import Prefetch,Q
from django.shortcuts import get_object_or_404
from django.db.models import Count
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.contrib.auth import get_user_model
CustomUser = get_user_model()


CustomUser = get_user_model()

@csrf_exempt
def google_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')
            print(token)
            # Verify the token with Google
            response = requests.get(f'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}')
            
            if response.status_code != 200:
                return JsonResponse({'error': 'Invalid token'}, status=400)
            
            user_data = response.json()
            # Now you can either create a new user or update an existing user's credentials
            user, created = CustomUser.objects.get_or_create(email=user_data['email'], defaults={
                'username': user_data['email'],
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', '')
            })
            
            # Here you would create a token for the user and return it to the frontend
            # For simplicity, let's assume you're using Django Rest Framework's token authentication
            # and you have a function to generate or retrieve the token for the user
            token, _ = Token.objects.get_or_create(user=user)
            
            return JsonResponse({'token': token.key})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
# Create your views here.
class SignUpView(APIView):
    def post(self,request):
        data=request.data
        email=data.get('email')
        username=data.get('username')
        fullname = data.get('fullname')
        password = data.get('password')

        if not email and not fullname and not username and not password:
            return Response({'error': 'Please Fill Required Fields'},status=status.HTTP_400_BAD_REQUEST)
        if not username or not username.strip(): 
            return Response({'error': 'Username cannot be blank or contain only spaces'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not fullname or not fullname.strip():
            return Response({'error': 'Full Name cannot be blank or contain only spaces '},status=status.HTTP_400_BAD_REQUEST)
        elif not (len(password) >= 8 and any(c.isupper() for c in password) and any(c.islower() for c in password) and any(c.isdigit() for c in password)):
            return Response({'error': 'Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit'},status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(email=email).exists():
            return Response({'error': 'Email Already Exists'}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': 'username Already Exists'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CustomUserSerializer(data=data)
        try:
            print("------------------tryblock-------------")
            serializer.is_valid(raise_exception=True)
            serializer.save()
            send_otp_email(serializer.data['email'])
            return Response({
                'status': 200,
                'message': 'Registration Successful, Check Email For Verification',
                'data': serializer.data
            })
        except Exception as e:
            print("------------------")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class Verify_Otp(APIView):
    def post(self,request):
        try:
            data=request.data
            print("Request.Data:",request.data)
            email=data.get('email')
            otp=data.get('otp')
            if not email or not otp:
                return Response({'error':'please enter otp'},status=status.HTTP_400_BAD_REQUEST)
            print("Otp:",otp,"---------","email:",email)
            serializer=VerifyUserSerializer(data=data)
            print(serializer)
            if serializer.is_valid():
                user=CustomUser.objects.get(email=email)
                if not user:
                    return Response({'error':'user not found'},status=status.HTTP_400_BAD_REQUEST)
                if user.otp != otp:
                    return Response({'error':'Invalid  otp'},status=status.HTTP_400_BAD_REQUEST)
                user.is_verified=True
                user.otp=None
                user.save()
                return Response({
                'status' : 200,
                'message' : 'Account Verified'

                })
            return Response({
                'status': 400,
                'message': 'Validation Error',
                'errors': serializer.errors
            })
        except Exception as e:
            print(e)
            return Response({
                'status': 500,
                'message': 'Internal Server Error'
            })
class  ResendOtpView(APIView):
    def post(self,request, *args, **kwargs):
        try:
            email=request.data.get('email')
            if email:
                user=CustomUser.objects.filter(email__iexact=email)
                if user.exists():
                    user = user.first()
                    new_otp = send_otp_email(email)
                    user.otp = new_otp
                    user.save()
                    return Response({
                        'message': 'New OTP sent successfully',
                        'status': status.HTTP_200_OK,
                    })

                else:
                    return Response({
                        'message': 'User not found ! Please register',
                        'status': status.HTTP_404_NOT_FOUND,
                    })
            else:
                return Response({
                    'message': 'Email is required',
                    'status': status.HTTP_400_BAD_REQUEST,
                })
        except Exception as e:
            return Response({
                'message': str(e),
                'status': status.HTTP_400_BAD_REQUEST,
            })     
# class LoginView(APIView):
#     def post(self,request):
#         email=request.data['email']
#         password=request.data['password']
#         provider = request.data.get('provider')
#         if not email:
#             return Response({'error':'Email is Required'},status=status.HTTP_400_BAD_REQUEST)
#         if not password:
#            return Response({'error':'Password is Required'},status=status.HTTP_400_BAD_REQUEST)

#         user=CustomUser.objects.filter(email=email).first()
#         print(user)
#         if user is None:
#             return Response({'error':'User Not found'},status=status.HTTP_400_BAD_REQUEST)

#         if not user.is_verified:
#             return Response({'error': 'User Is not verified'},status=status.HTTP_400_BAD_REQUEST)
#         if not user.is_active:
#             return Response({'error': 'User is blocked'}, status=status.HTTP_403_FORBIDDEN)
#         if not user.check_password(password):
#             return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
        

        
#         if user.is_superuser == True:
#             return Response({'error': 'Admin Cannot access'},status=status.HTTP_400_BAD_REQUEST)    
#         payload={
#             'id':user.id,
#             'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=60),
#             'iat': datetime.datetime.now(datetime.timezone.utc),
#         }
#         token = jwt.encode(payload, 'secret', algorithm='HS256')
#         response = Response()

#         response.data = {
#             'user':{
#                 'id':user.id,
#                 'email':user.email,
#             },
#             'jwt': token,
#             'message': 'Login Success'
#         }
#         return response
class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']
        if not email:
            return Response({'error': 'Email is Required'}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'error': 'Password is Required'}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.filter(email=email).first()
        if user is None:
            return Response({'error': 'User Not found'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_verified:
            return Response({'error': 'User Is not verified'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({'error': 'User is blocked'}, status=status.HTTP_403_FORBIDDEN)
        if not user.check_password(password):
            return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
        if user.is_superuser:
            return Response({'error': 'Admin Cannot access'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate Access Token
        access_payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1),  # Access token expires in 60 minutes
            'iat': datetime.datetime.utcnow(),
        }
        access_token = jwt.encode(access_payload, 'secret', algorithm='HS256')

        # Generate Refresh Token
        refresh_payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),  # Refresh token expires in 7 days
            'iat': datetime.datetime.utcnow(),
        }
        refresh_token = jwt.encode(refresh_payload, 'secret', algorithm='HS256')

        # Here you should save the refresh token associated with the user in your storage (database, cache, etc.)

        response = Response()
        response.data = {
            'user': {
                'id': user.id,
                'email': user.email,
            },
            'jwt': access_token,
            'refresh_token': refresh_token,  # Include the refresh token in the response
            'message': 'Login Success'
        }
        return response
class userView(APIView):
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]
    def get(self, request):
        auth_header = request.headers.get('Authorization')
        print("====",request.user)

        if not auth_header or 'Bearer ' not in auth_header:
            raise AuthenticationFailed("Not authorized")
        token = auth_header.split('Bearer ')[1]
        try:
            payload = jwt.decode(token, 'secret', algorithms=["HS256"])
            print("Decoded Payload:", payload)
            user = CustomUser.objects.filter(id=payload['id']).first()
            user_serializer = CustomUserSerializer(user)
            
            user_profile = UserProfile.objects.filter(user=user).first()
            user_profile_serializer = UserProfileSerializer(user_profile)
            
            response_data = {
                'user':user_serializer.data,
                'user_profile' :user_profile_serializer.data
            }
            
            return Response(response_data)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Not authorized")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

    
class UserLogout(APIView):
    def post(self,request):
        response=Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        
        return response
class UserProfileDetailView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_object(self):
        user_id = self.kwargs['user_id']
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User Not Found"}, status=status.HTTP_400_BAD_REQUEST)
    
class UserProfileUpdate(APIView):
    def post(self, request, user_id):  # sourcery skip: extract-duplicate-method
        username = request.data.get('username')
        location = request.data.get('location')
        bio = request.data.get('bio')
        profile_photo = request.FILES.get('profile_photo')
        cover_photo = request.FILES.get('cover_photo')
        date_of_birth = request.data.get('date_of_birth')

        print("given data--", username, bio, location, date_of_birth)
        print("Given Photos", profile_photo, "---------", cover_photo)

        user = CustomUser.objects.filter(id=user_id).first()

        if user:
            user.username = username
            user.save()

            user_profile = UserProfile.objects.filter(user=user).first()

            if user_profile:
                user_profile.location = location
                user_profile.date_of_birth = date_of_birth
                user_profile.bio = bio

                if "profile_photo" in request.FILES:
                    user_profile.profile_image = profile_photo

                if "cover_photo" in request.FILES:
                    user_profile.cover_photo = cover_photo

                user_profile.save()

                return Response({"message": "User Updated Successfully"})


            else:
                new_user_profile = UserProfile.objects.create(
                    user=user,
                    location=location,
                    date_of_birth=date_of_birth,
                    bio=bio,
                )

                if "profile_photo" in request.FILES:
                    new_user_profile.profile_image = profile_photo

                if "cover_photo" in request.FILES:
                    new_user_profile.cover_photo = cover_photo

                new_user_profile.save()

                return Response({"message": "New User Created Successfully"}, status=status.HTTP_201_CREATED)

        else:
            return Response({"Error": "User Not Found"})
           

class PostCreateAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)#for handling multipart data

    def post(self, request, id, *args, **kwargs):
        print("Adding Post")
        try:
            user = CustomUser.objects.get(id=id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User Not Found"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PostSerializer(data=request.data) #for validating
        print(serializer.is_valid())
        if serializer.is_valid():#check serializer is valid
            validated_data = serializer.validated_data
            print("Validated_data:",validated_data)
            validated_data['user'] = user#add user to validated data
            post = serializer.save(**validated_data) #save post using serializer
            print("----",request.data)
            try:
                images_data = request.FILES.getlist('images[0]')
                for image in images_data:
                    PostImage.objects.create(post=post, images_url=image)#retrive images and videos

                videos_data = request.FILES.getlist('videos[0]')
                for video in videos_data:
                    PostVideo.objects.create(post=post, video_url=video)

                post_serialized = PostSerializer(post) #serializes the post to convert to json
                print("Received files:", request.FILES)
                print(post_serialized)
                return Response(post_serialized.data, status=status.HTTP_201_CREATED)
            except ValidationError as ve:
                print("Validation Error:", ve)
                return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("Unexpected Error:", e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print("Error:",serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
class UserPostListAPIView(APIView):
    """
    API View to list all posts created by a specific user.
    """
    def get(self, request, user_id, format=None):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        posts = Post.objects.filter(user=user, is_deleted=False).prefetch_related('postimage_set', 'postvideo_set')\
            .order_by('-created_at') #desplay in desending order
        print("Posts:",posts)
        serializer = PostSerializer(posts, many=True) #to serialize multiple post
        print(serializer.data)
        return Response(serializer.data)
    
    

class PostUpdateAPIView(APIView):
    
    print("------------")
    
    def process_files(self, post, images_data, videos_data):
        for image in images_data:
            PostImage.objects.create(post=post, images_url=image)

        for video in videos_data:
            PostVideo.objects.create(post=post, video_url=video)

    def put(self, request, post_id, *args, **kwargs):
        print(request.data)
        post = get_object_or_404(Post, id=post_id, *args, **kwargs)
        serializer = PostSerializer(post, data=request.data)
        
        print(serializer.is_valid())

        if serializer.is_valid():
            try:
                images_data = request.FILES.getlist('images[0]')
                videos_data = request.FILES.getlist('videos[0]')
                if images_data:
                    for image in images_data:
                        PostImage.objects.create(post=post, images_url=image)
                if videos_data:
                    for video in videos_data:
                        PostVideo.objects.create(post=post, video_url=video)
                print("Received Files:",request.FILES)

                # Save the updated content
                serializer.save()

                post_serialized = PostSerializer(post)
                return Response(post_serialized.data, status=status.HTTP_200_OK)
            except ValidationError as ve:
                return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    
    def delete(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id, *args, **kwargs)
        post.is_deleted = True
        post.save()
        return Response({"message": "Post deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
