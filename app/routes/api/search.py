import logging
from flask import Blueprint, request, jsonify
from app.services import search_service

search_bp = Blueprint('search', __name__)

def init_routes(limiter=None):
    """初始化搜索相关路由"""

    @search_bp.route('/api/search', methods=['GET'])
    def search_notes():
        """搜索笔记内容"""
        query = request.args.get('q', '')
        if not query or len(query.strip()) < 2:
            return jsonify([])

        results = search_service.search_notes(query.strip())
        return jsonify(results)

    return search_bp
