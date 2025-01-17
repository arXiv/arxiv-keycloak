import unittest
import requests

port = 21505
legacy_api_token = 'legacy-api-token'
headers = {
            'Content-Type': 'application/json',
            'authorization': f'Bearer {legacy_api_token}'
        }

class TestLogin(unittest.TestCase):
    def test_auth_get(self):
        response = requests.get(f'http://localhost:{port}/auth/qaServiceAccount',
                                headers=headers)
        self.assertEqual(200, response.status_code)

    def test_auth_post(self):
        response = requests.post(f'http://localhost:{port}/auth/qaServiceAccount',
                                 json={"password": "changeme"},
                                 headers=headers)
        self.assertEqual(200, response.status_code)

if __name__ == '__main__':
    unittest.main()
