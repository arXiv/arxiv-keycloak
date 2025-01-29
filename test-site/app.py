"""
Small Flask app

"""
import json
import os

from flask import Flask, redirect, session, url_for, render_template, request
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.auth.auth.middleware import AuthMiddleware
from arxiv.auth.auth import Auth
from arxiv.base.middleware import wrap


class FlaskFixture(Flask):
    def __init__(self, *args: [], **kwargs: dict):
        super().__init__(*args, **kwargs)
        assert os.environ.get('JWT_SECRET')
        assert os.environ.get('KC_URL_PUBLIC')
        assert os.environ.get('KEYCLOAK_TEST_CLIENT_SECRET')
        assert os.environ.get('NGINX_PORT')

        self.secret_key = os.environ['KEYCLOAK_TEST_CLIENT_SECRET']
        nginx_port = os.environ['NGINX_PORT']
        self.jwt_secret = os.environ.get('JWT_SECRET')
        self.idp = ArxivOidcIdpClient(f"http://localhost:{nginx_port}/aaa/callback",
                                      scope=["openid"],
                                      server_url=os.environ['KC_URL_PUBLIC'],
                                      client_id="arxiv-user"
                                      )

app = FlaskFixture(__name__)

def get_user_claims():
    arxiv_access_token = request.cookies.get('arxiv_oidc_session')
    username = ""
    email = ""
    claims = None
    if arxiv_access_token:
        tokens, jwt_payload = ArxivUserClaims.unpack_token(arxiv_access_token)
        username = tokens['sub']

        try:
            claims = ArxivUserClaims.decode_jwt_payload(tokens, jwt_payload, app.jwt_secret)
        except Exception as e:
            pass

        if claims:
            email = claims.email
    return username, email


@app.route('/')
def home():
    username, email = get_user_claims()
    return render_template('home.html', username=username, email=email)

@app.route('/login')
def login():
    return redirect("/aaa/login?next_page=/protected")

@app.route('/logout')
def logout():
    # Clear the session and redirect to home
    session.clear()
    return redirect("/aaa/logout?next_page=/")

@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')

@app.route('/protected')
def protected():
    username, email = get_user_claims()
    if not username:
        return redirect(url_for('unauthorized'))
    return render_template('user.html', username=username, email=email)

def create_app():
    return app

if __name__ == '__main__':
    Auth(app)
    wrap(app, [AuthMiddleware])
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 21509))
