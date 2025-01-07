import unittest
import requests


port = 21501

class TestLogin(unittest.TestCase):
    def test_auth_get(self):
        response = requests.get(f'http://localhost:{port}/auth/qaServiceAccount')
        self.assertEqual(200, response.status_code)

    def test_auth_post(self):
        response = requests.post(f'http://localhost:{port}/auth/qaServiceAccount',
                                 json={"password": "changeme"})
        self.assertEqual(200, response.status_code)

if __name__ == '__main__':
    unittest.main()
