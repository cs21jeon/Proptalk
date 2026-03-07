"""
관리자 대시보드 라우트
- ADMIN_EMAIL 환경변수와 일치하는 사용자만 접근 가능
"""
import logging
import requests as http_requests
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, g, render_template, redirect, session
from auth import login_required, decode_token
from config import Config
from models import User, query_one
from models_billing import (
    UserBilling, PaymentTransaction, UsageLog, AdminQueries, BillingPlan
)

logger = logging.getLogger(__name__)


def admin_required(f):
    """관리자 전용 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        # JWT from session (web pages)
        if not token:
            token = session.get('admin_token')

        if not token:
            return redirect('/proptalk/admin/login')

        payload = decode_token(token)
        if not payload:
            session.pop('admin_token', None)
            return redirect('/proptalk/admin/login')

        user = User.find_by_id(payload['user_id'])
        if not user or user['email'] != Config.ADMIN_EMAIL:
            return jsonify({'error': 'Forbidden'}), 403

        g.user = user
        g.user_id = user['id']
        return f(*args, **kwargs)
    return decorated


def register_admin_routes(app):

    @app.route('/proptalk/admin/login', methods=['GET'])
    def admin_login_page():
        if not Config.ADMIN_EMAIL:
            return 'Admin not configured', 404
        # 토큰이 query param으로 전달되면 자동 로그인
        token = request.args.get('token')
        if token:
            payload = decode_token(token)
            if payload:
                user = User.find_by_id(payload['user_id'])
                if user and user['email'] == Config.ADMIN_EMAIL:
                    session['admin_token'] = token
                    return redirect('/proptalk/admin/')
        return render_template('admin/login.html', google_client_id=Config.GOOGLE_CLIENT_ID)

    @app.route('/proptalk/admin/login', methods=['POST'])
    def admin_login_post():
        if not Config.ADMIN_EMAIL:
            return jsonify({'error': 'Admin not configured'}), 404

        data = request.get_json() or request.form
        google_token = data.get('id_token', '').strip()

        if not google_token:
            return jsonify({'error': 'Google sign-in required'}), 400

        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            idinfo = google_id_token.verify_oauth2_token(
                google_token, google_requests.Request(), Config.GOOGLE_CLIENT_ID
            )
            email = idinfo.get('email', '')
        except Exception:
            return jsonify({'error': 'Invalid Google token'}), 401

        if email != Config.ADMIN_EMAIL:
            return jsonify({'error': '관리자 계정이 아닙니다'}), 403

        user = query_one("SELECT * FROM users WHERE email = %s", (email,))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        from auth import create_token
        token = create_token(user['id'])
        session['admin_token'] = token
        return jsonify({'ok': True, 'redirect': '/proptalk/admin/'})

    @app.route('/proptalk/admin/logout')
    def admin_logout():
        session.pop('admin_token', None)
        return redirect('/proptalk/admin/login')

    @app.route('/proptalk/admin/')
    @admin_required
    def admin_dashboard():
        stats = AdminQueries.get_stats()
        recent = AdminQueries.recent_transactions(10)

        return render_template('admin/dashboard.html',
                               stats=stats, recent=recent)

    @app.route('/proptalk/admin/users')
    @admin_required
    def admin_users():
        users = AdminQueries.list_users_with_billing()
        return render_template('admin/users.html', users=users)

    @app.route('/proptalk/admin/users/<int:user_id>')
    @admin_required
    def admin_user_detail(user_id):
        user = User.find_by_id(user_id)
        if not user:
            return 'User not found', 404
        billing = UserBilling.find_by_user_id(user_id)
        transactions = PaymentTransaction.list_for_user(user_id)
        usage = UsageLog.list_for_user(user_id)
        plans = BillingPlan.list_active()
        return render_template('admin/user_detail.html',
                               user=user, billing=billing,
                               transactions=transactions, usage=usage,
                               plans=plans)

    @app.route('/proptalk/admin/api/users/<int:user_id>/plan', methods=['POST'])
    @admin_required
    def admin_change_plan(user_id):
        """사용자 요금제/잔여시간 변경"""
        data = request.get_json()
        action = data.get('action')

        if action == 'add_seconds':
            seconds = int(data.get('seconds', 0))
            if seconds > 0:
                UserBilling.ensure(user_id)
                UserBilling.add_seconds(user_id, seconds)
                logger.info(f"[Admin] user={user_id} +{seconds}s by {g.user['email']}")

        elif action == 'set_plan':
            plan_code = data.get('plan_code')
            plan = BillingPlan.find_by_code(plan_code)
            if plan:
                UserBilling.ensure(user_id)
                from models import execute
                execute(
                    "UPDATE user_billing SET current_plan_id = %s WHERE user_id = %s",
                    (plan['id'], user_id)
                )
                logger.info(f"[Admin] user={user_id} plan={plan_code} by {g.user['email']}")

        elif action == 'set_seconds':
            seconds = int(data.get('seconds', 0))
            UserBilling.ensure(user_id)
            from models import execute
            execute(
                "UPDATE user_billing SET remaining_seconds = %s WHERE user_id = %s",
                (seconds, user_id)
            )
            logger.info(f"[Admin] user={user_id} set_seconds={seconds} by {g.user['email']}")

        return jsonify({'ok': True})
