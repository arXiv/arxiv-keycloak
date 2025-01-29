"""
Small Flask app as test fixture.

The fixture assumes that the docker compose is up and all the services running.

"""
import json
import os

from flask import Flask, redirect, request, session, url_for, jsonify
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.auth.auth.middleware import AuthMiddleware
from arxiv.auth.auth import Auth
from arxiv.base.middleware import wrap
from dotenv import load_dotenv, dotenv_values

KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', 'http://localhost:21501')

class FlaskFixture(Flask):
    def __init__(self, *args: [], **kwargs: dict):
        bend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        arxiv_keycloak_dir = os.path.dirname(bend_dir)
        super().__init__(*args, **kwargs)
        assert load_dotenv(dotenv_path=os.path.join(arxiv_keycloak_dir, ".env"))
        self.env = dotenv_values()
        self.secret_key = self.env['KEYCLOAK_TEST_CLIENT_SECRET']
        nginx_port = self.env['NGINX_PORT']
        self.idp = ArxivOidcIdpClient(f"http://localhost:{nginx_port}/aaa/callback",
                                      scope=["openid"],
                                      server_url=self.env['KC_URL_PUBLIC'],
                                      client_id="arxiv-user"
                                      )

app = FlaskFixture(__name__)

@app.route('/')
def home():
    session.clear()
    return redirect('/login')

@app.route('/login')
def login():
    return redirect(app.idp.login_url)


@app.route('/callback')
def callback():
    # Get the authorization code from the callback URL
    code = request.args.get('code')
    user_claims = app.idp.from_code_to_user_claims(code)

    if user_claims is None:
        session.clear()
        return 'Something is wrong'

    print(user_claims._claims)
    session["access_token"] = user_claims.to_arxiv_token_string
    return 'Login successful!'


@app.route('/logout')
def logout():
    # Clear the session and redirect to home
    session.clear()
    return redirect(url_for('home'))


@app.route('/protected')
def protected():
    arxiv_access_token = session.get('access_token')
    if not arxiv_access_token:
        return redirect(app.idp.login_url)
    claims = ArxivUserClaims(json.loads(arxiv_access_token))
    if claims.is_admin:
        return jsonify({'message': 'Token is valid', 'claims': json.dumps(claims._claims)})
    return jsonify({'message': 'Not admin', 'claims': json.dumps(claims._claims)})


def create_app():
    return app

if __name__ == '__main__':
    os.environ['JWT_SECRET'] = app.env['JWT_SECRET']
    Auth(app)
    wrap(app, [AuthMiddleware])
    app.run(debug=True, host='0.0.0.0', port=5101)
