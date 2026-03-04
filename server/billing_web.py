"""
웹 결제 페이지 라우트 (HTML 렌더링)
앱에서 url_launcher로 열리는 결제 웹페이지
"""
import logging
from flask import render_template, request, redirect
from config import Config

logger = logging.getLogger(__name__)


def register_billing_web_routes(app):

    @app.route('/proptalk/billing/')
    def billing_page():
        """요금제 선택 페이지"""
        return render_template(
            'billing/plans.html',
            toss_client_key=Config.TOSS_CLIENT_KEY,
        )

    @app.route('/proptalk/billing/checkout')
    def billing_checkout():
        """Toss SDK 결제 페이지"""
        return render_template(
            'billing/checkout.html',
            toss_client_key=Config.TOSS_CLIENT_KEY,
        )

    @app.route('/proptalk/billing/success')
    def billing_success():
        """결제 성공 페이지"""
        return render_template('billing/success.html')

    @app.route('/proptalk/billing/fail')
    def billing_fail():
        """결제 실패 페이지"""
        return render_template('billing/fail.html')

    @app.route('/proptalk/billing/manage')
    def billing_manage():
        """구독 관리 페이지"""
        return render_template('billing/manage.html')
