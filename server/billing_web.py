"""
웹 결제 페이지 라우트 (HTML 렌더링)
앱에서 url_launcher로 열리는 결제 웹페이지
+ 랜딩페이지 서빙
"""
import os
import logging
from flask import render_template, request, redirect, send_from_directory
from config import Config

logger = logging.getLogger(__name__)

# 프로젝트 루트 (server/ 의 상위)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def register_billing_web_routes(app):

    # ── 랜딩페이지 ──
    @app.route('/proptalk/')
    def proptalk_landing():
        """Proptalk 랜딩페이지 (Coming Soon)"""
        return send_from_directory(
            os.path.join(_PROJECT_ROOT, 'marketing', 'proptalk'),
            'index.html',
        )

    @app.route('/proptalk/images/<path:filename>')
    def proptalk_images(filename):
        """랜딩페이지용 이미지 서빙"""
        return send_from_directory(
            os.path.join(_PROJECT_ROOT, 'images'),
            filename,
        )

    # ── 법적 문서 페이지 ──
    _MARKETING_DIR = os.path.join(_PROJECT_ROOT, 'marketing', 'proptalk')

    @app.route('/proptalk/terms')
    def proptalk_terms():
        """이용약관"""
        return send_from_directory(_MARKETING_DIR, 'terms-of-service.html')

    @app.route('/proptalk/privacy')
    def proptalk_privacy():
        """개인정보 처리방침"""
        return send_from_directory(_MARKETING_DIR, 'privacy-policy.html')

    @app.route('/proptalk/payment-terms')
    def proptalk_payment_terms():
        """결제/환불 약관"""
        return send_from_directory(_MARKETING_DIR, 'billing-terms.html')

    # ── 결제 페이지 ──
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
