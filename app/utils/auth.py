import hashlib
import hmac
from functools import wraps
from flask import request, abort
from app.config.config_manager import config

def get_secure_hash(string, key):
    """使用 HMAC-SHA256 生成安全哈希"""
    return hmac.new(
        key.encode(),
        string.encode(),
        hashlib.sha256
    ).hexdigest()

def check_auth(headers):
    """验证请求认证信息,与原版保持一致"""
    nonce = headers.get('x-sharenote-nonce', '')
    key = headers.get('x-sharenote-key', '')
    api_key = nonce + config.get('security.secret_api_key')
    
    hash_object = hashlib.sha256(api_key.encode())
    digest = hash_object.hexdigest()
    return digest == key

def require_auth(f):
    """装饰器:要求认证"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth(request.headers):
            abort(401)
        return f(*args, **kwargs)
    return decorated