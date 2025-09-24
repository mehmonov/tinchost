from fastapi import Request, HTTPException, status
import httpx
from starlette.middleware.sessions import SessionMiddleware
from config import config
from models.user import User
import secrets

# https://gist.github.com/pelson/47c0c89a3522ed8da5cc305afc2562b0
# https://medium.com/@bhuwan.pandey9867/github-authentication-with-python-fastapi-446a20e60d5a


class AuthManager:
    @staticmethod
    async def get_github_auth_url(request: Request) -> str:
        redirect_uri = config.GITHUB_REDIRECT_URI
        state = secrets.token_urlsafe(32)
        request.session['oauth_state'] = state
        
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={config.GITHUB_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=user:email"
            f"&state={state}"
        )
    
    @staticmethod
    async def handle_github_callback(request: Request) -> User:
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')
        
        if error:
            raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error}")
        
        session_state = request.session.get('oauth_state')
        if state != session_state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'client_id': config.GITHUB_CLIENT_ID,
                    'client_secret': config.GITHUB_CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': config.GITHUB_REDIRECT_URI
                },
                headers={'Accept': 'application/json'}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail=f"GitHub token request failed: {token_response.status_code}"
                )
            
            token_data = token_response.json()
            
            if 'error' in token_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"GitHub OAuth error: {token_data.get('error_description', token_data['error'])}"
                )
            
            if 'access_token' not in token_data:
                raise HTTPException(
                    status_code=400, 
                    detail="Access token not found in response"
                )
            
            access_token = token_data['access_token']
            
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            user_data = user_response.json()
            
            email_response = await client.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            emails = email_response.json()
            primary_email = next((email['email'] for email in emails if email['primary']), None)
        
        github_id = user_data['id']
        username = user_data['login']
        avatar_url = user_data.get('avatar_url')
        
        user = User.get_by_github_id(github_id)
        if not user:
            user = User(
                github_id=github_id,
                username=username,
                email=primary_email,
                avatar_url=avatar_url
            )
        else:
            user.username = username
            user.email = primary_email
            user.avatar_url = avatar_url
        user.save()
        
        request.session.pop('oauth_state', None)
        
        return user
    
    @staticmethod
    def create_session(request: Request, user: User):
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        request.session['is_admin'] = user.is_admin
    
    @staticmethod
    def get_current_user(request: Request) -> User | None:
        user_id = request.session.get('user_id')
        if not user_id:
            return None
        return User.get_by_id(user_id)
    
    @staticmethod
    def logout(request: Request):
        request.session.clear()
    
    @staticmethod
    def require_auth(request: Request) -> User:
        user = AuthManager.get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return user
    
    @staticmethod
    def require_admin(request: Request) -> User:
        user = AuthManager.get_current_user(request)
        
        if user and user.is_admin:
            return user
        
        admin_username = request.session.get('admin_username')
        if admin_username == config.ADMIN_USERNAME:
            admin_user = User(
                username=config.ADMIN_USERNAME,
                email="admin@tinchost.uz",
            )
            return admin_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    @staticmethod
    def admin_login(request: Request, username: str, password: str) -> bool:
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            request.session['admin_username'] = username
            return True
        return False
    
    @staticmethod
    def admin_logout(request: Request):
        request.session.pop('admin_username', None)

def get_session_middleware():
    return SessionMiddleware(secret_key=config.SECRET_KEY) # Pylance says the parameter app is missing
