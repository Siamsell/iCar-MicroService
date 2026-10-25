from rest_framework import authentication, exceptions
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class StatelessJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        
        if not token:
            return None
        
        try:
            access_token = AccessToken(token)
            
            user_id = access_token.payload.get('user_id')
            user_name = access_token.payload.get('name')
            
            if not user_id and not user_name:
                raise exceptions.AuthenticationFailed('Invalid token: no user_id')
            
           
                
            user = type('User', (), {
                'id': user_id,
                'name':user_name,
                'is_authenticated': True
            })()
            return (user, token)
            
        except InvalidToken:
            raise exceptions.AuthenticationFailed('Invalid token')
        except TokenError as e:
            raise exceptions.AuthenticationFailed(str(e))

class IsAuthenticatedStateless(BasePermission):
    def has_permission(self, request, view):
        return request.user and hasattr(request.user, 'is_authenticated')