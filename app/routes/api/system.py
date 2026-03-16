import time
import logging
from flask import Blueprint, jsonify, abort
from app.utils.auth import require_auth
from app.services import monitor_service

system_bp = Blueprint('system', __name__)

def init_routes(limiter=None):
    """初始化系统监控相关路由"""

    @system_bp.route('/api/system/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time()
        })

    @system_bp.route('/api/system/stats', methods=['GET'])
    @require_auth
    def system_stats():
        """获取系统状态"""
        return jsonify(monitor_service.get_system_stats())

    @system_bp.route('/api/system/storage', methods=['GET'])
    @require_auth
    def storage_stats():
        """获取存储统计信息"""
        return jsonify(monitor_service.get_storage_stats())

    @system_bp.route('/v1/account/get-key', methods=['GET'])
    def get_key():
        return 'Please set your API key in the Share Note plugin settings to the one set in settings.toml'

    return system_bp
