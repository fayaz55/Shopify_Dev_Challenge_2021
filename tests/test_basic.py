  # tests/test_basic.py

import unittest
from ..app import app

class FlaskTestCase(unittest.TestCase):

    # Ensure that Flask was set up correctly
    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        response = self.client.get('/login', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    # Ensure that dashboard page requires user login
    def test_dashboard_requires_login(self):
        
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)

    # Ensure that welcome page loads
    def test_welcome_route_works_as_expected(self):
        response = self.client.get('/welcome', follow_redirects=True)
        self.assertIn(b'Welcome to Flask!', response.data)

    # Ensure that posts show up on the main page
    # def test_posts_show_up_on_main_page(self):
    #     response = self.client.post(
    #         '/login',
    #         data=dict(username="admin", password="admin"),
    #         follow_redirects=True
    #     )
    #     self.assertIn(b'This is a test. Only a test.', response.data)


if __name__ == '__main__':
    unittest.main()