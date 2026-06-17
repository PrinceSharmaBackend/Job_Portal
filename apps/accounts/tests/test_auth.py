from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User


class RegisterTestCase(APITestCase):
    url = reverse('auth-register')

    def get_payload(self, **kwargs):
        data = {
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'job_seeker',
            'password': 'StrongPass@123',
            'confirm_password': 'StrongPass@123',
        }
        data.update(kwargs)
        return data

    def test_register_job_seeker_success(self):
        res = self.client.post(self.url, self.get_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', res.data)
        self.assertEqual(User.objects.count(), 1)

    def test_register_employer_success(self):
        res = self.client.post(self.url, self.get_payload(role='employer', email='emp@example.com'), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_register_password_mismatch(self):
        res = self.client.post(self.url, self.get_payload(confirm_password='WrongPass'), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', res.data)

    def test_register_duplicate_email(self):
        self.client.post(self.url, self.get_payload(), format='json')
        res = self.client.post(self.url, self.get_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        res = self.client.post(self.url, {'email': 'x@x.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='login@example.com',
            password='StrongPass@123',
            first_name='Login',
            last_name='User',
        )
        self.url = reverse('auth-login')

    def test_login_success(self):
        res = self.client.post(self.url, {'email': 'login@example.com', 'password': 'StrongPass@123'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertIn('user', res.data)

    def test_login_wrong_password(self):
        res = self.client.post(self.url, {'email': 'login@example.com', 'password': 'wrongpass'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        res = self.client.post(self.url, {'email': 'nobody@example.com', 'password': 'pass'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='logout@example.com',
            password='StrongPass@123',
            first_name='Logout',
            last_name='User',
        )
        login_res = self.client.post(reverse('auth-login'), {
            'email': 'logout@example.com', 'password': 'StrongPass@123'
        }, format='json')
        self.access = login_res.data['access']
        self.refresh = login_res.data['refresh']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_logout_success(self):
        res = self.client.post(reverse('auth-logout'), {'refresh': self.refresh}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_logout_without_refresh_token(self):
        res = self.client.post(reverse('auth-logout'), {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class MeTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='me@example.com',
            password='StrongPass@123',
            first_name='Me',
            last_name='User',
        )
        login_res = self.client.post(reverse('auth-login'), {
            'email': 'me@example.com', 'password': 'StrongPass@123'
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_res.data["access"]}')

    def test_get_my_profile(self):
        res = self.client.get(reverse('auth-me'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'me@example.com')

    def test_update_my_profile(self):
        res = self.client.patch(reverse('auth-me'), {'first_name': 'Updated'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        self.client.credentials()
        res = self.client.get(reverse('auth-me'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password(self):
        res = self.client.post(reverse('change-password'), {
            'old_password': 'StrongPass@123',
            'new_password': 'NewPass@456',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_old(self):
        res = self.client.post(reverse('change-password'), {
            'old_password': 'wrongpassword',
            'new_password': 'NewPass@456',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
