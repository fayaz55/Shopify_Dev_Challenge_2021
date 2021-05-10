from app import app
import unittest
from app import RegisterForm
from io import BytesIO

class FlaskTestCase(unittest.TestCase):

    #Ensure that flask was set up correctly
    def test_index(self):
        tester=app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)
    
    #Ensure that login page works
    def test_login(self):
        tester=app.test_client(self)
        response = tester.get('/login', content_type='html/text')
        self.assertEqual(response.status_code, 200)
    
    #Ensure register page works
    def test_register(self):
        tester=app.test_client(self)
        response = tester.get('/register', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    # Ensure that Dashboard page requires user login
    def test_dashboard_requires_login(self):
        tester=app.test_client(self)
        response = tester.get('/dashboard', follow_redirects=True)
        self.assertTrue(b'Login' in response.data)

    # Ensure that Upload page requires user login
    def test_upload_requires_login(self):
        tester=app.test_client(self)
        response = tester.get('/upload', follow_redirects=True)
        self.assertTrue(b'Login' in response.data)
    
    # Ensure that Upload page requires user login
    def test_upload_requires_login(self):
        tester=app.test_client(self)
        response = tester.get('/upload', follow_redirects=True)
        self.assertIn(b'Login',response.data)

    # Test that correct login goes to the dashboard
    def test_correct_login(self):
        tester=app.test_client(self)
        response=tester.post(
            '/login', 
            data=dict(username="amy1", password="amy1"), 
            follow_redirects=True
        )
        self.assertIn(b'Dashboard',response.data)
    
    # Test that the incorrect login redirects to the login page
    def test_incorrect_login(self):
        tester=app.test_client(self)
        response=tester.post(
            '/login', 
            data=dict(username="amy1", password="amy2"), 
            follow_redirects=True
        )
        self.assertIn(b'Login',response.data)

    # test if an invalid username (does not exist) redirects to the login page
    def test_wrong_username_login(self):
        tester=app.test_client(self)
        response=tester.post(
            '/login', 
            data=dict(username="amy2", password="amy2"), 
            follow_redirects=True
        )
        self.assertIn(b'Login',response.data)
    
    # Test that succesful register goes to login page and can access dashboard
    def test_register_success(self):
        tester=app.test_client(self)
        response=tester.post(
            '/register', 
            data=dict(name="gold",username="gold", password="gold",confirm="gold", email="gold@gmail.com"), 
            follow_redirects=True
        )
        self.assertTrue(b'Login' in response.data)
        response1=tester.post(
            '/login', 
            data=dict(username="gold", password="gold"), 
            follow_redirects=True
        )
        self.assertIn(b'Dashboard',response1.data)
    
    # Ensure and check if passwords do not match works
    def test_register_failure(self):
        tester=app.test_client(self)
        response=tester.post(
            '/register', 
            data=dict(name="amy1",username="amy1", password="amy2", confirm="amy1", email="amy1@gmail.com"), 
            follow_redirects=True
        )
        self.assertTrue(b'Passwords do not match' in response.data)

    # Ensure and check if username exists already works
    def test_register_failure(self):
        tester=app.test_client(self)
        response=tester.post(
            '/register', 
            data=dict(name="amy1",username="amy1", password="amy1", confirm="amy1", email="amy1@gmail.com"), 
            follow_redirects=True
        )
        self.assertTrue(b'Username Exists' in response.data)
    
    # Ensure successful logout
    def test_logout(self):
        tester = app.test_client(self)
        tester.post(
            '/login', 
            data=dict(username="amy1", password="amy1"), 
            follow_redirects=True
        )
        response=tester.get('/logout', follow_redirects=True)
        self.assertFalse(b'Upload'in response.data)
    
    # Ensure upload page available after login
    def test_upload(self):
        tester = app.test_client(self)
        tester.post(
            '/login', 
            data=dict(username="amy1", password="amy1"), 
            follow_redirects=True
        )
        response=tester.get('/upload', follow_redirects=True)
        self.assertIn(b'Visibility', response.data)
    
    def test_upload_image(self):

        tester = app.test_client(self)
        tester.post(
            '/login', 
            data=dict(username="amy1", password="amy1"), 
            follow_redirects=True
        )

        response =tester.post(
            '/upload',
            content_type='multipart/form-data',
            data={ 'visibility': '0',
                'image':[ (BytesIO(b'FILE CONTENT') ,'')]
                },
            follow_redirects=True
        )
        self.assertEquals(response.status, "200 OK")
    


if __name__ == '__main__':
    unittest.main()
    