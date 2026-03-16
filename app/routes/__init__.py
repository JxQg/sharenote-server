"""
Routes package - 路由注册入口
"""
from app.routes.api.notes import notes_bp, init_routes as init_notes_routes
from app.routes.api.assets import assets_bp, init_routes as init_assets_routes
from app.routes.api.search import search_bp, init_routes as init_search_routes
from app.routes.api.system import system_bp, init_routes as init_system_routes
from app.routes.api.views import views_bp, init_routes as init_views_routes

def register_routes(app, limiter=None):
    """注册所有路由模块"""

    # 初始化各模块路由（传入 limiter）
    init_notes_routes(limiter)
    init_assets_routes(limiter)
    init_search_routes(limiter)
    init_system_routes(limiter)
    init_views_routes(limiter)

    # 注册蓝图
    app.register_blueprint(notes_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(views_bp)
