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
    """验证请求头中的认证信息"""
    nonce = headers.get('x-sharenote-nonce')
    key = headers.get('x-sharenote-key')
    api_key = config.get('security.secret_api_key')
    
    if not all([nonce, key, api_key]):
        return False
        
    expected_key = get_secure_hash(nonce, api_key)
    return hmac.compare_digest(expected_key, key)

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth(request.headers):
            abort(401)
        return f(*args, **kwargs)
    return decorated