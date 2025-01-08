"""
Small Flask app

"""
import json
import os

from flask import Flask, redirect, session, url_for, render_template
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
        assert os.environ.get('KEYCLOAK_CLIENT_SECRET')
        assert os.environ.get('NGINX_PORT')

        self.secret_key = os.environ['KEYCLOAK_CLIENT_SECRET']
        nginx_port = os.environ['NGINX_PORT']
        self.idp = ArxivOidcIdpClient(f"http://localhost:{nginx_port}/aaa/callback",
                                      scope=["openid"],
                                      server_url=os.environ['KC_URL_PUBLIC'],
                                      client_id="arxiv-user"
                                      )

app = FlaskFixture(__name__)

@app.route('/')
def home():
    session.clear()
    return render_template('home.html')

@app.route('/login')
def login():
    return redirect(app.idp.login_url)

@app.route('/logout')
def logout():
    # Clear the session and redirect to home
    session.clear()
    return redirect(url_for('home'))


@app.route('/protected')
def protected():
    arxiv_access_token = session.get('arxiv-oidc-cookie')
    if not arxiv_access_token:
        return redirect(app.idp.login_url)
    claims = ArxivUserClaims(json.loads(arxiv_access_token))
    return render_template('user.html', username=claims.name, email=claims.email)

def create_app():
    return app

if __name__ == '__main__':
    Auth(app)
    wrap(app, [AuthMiddleware])
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 21509))
