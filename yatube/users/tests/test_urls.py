from http import HTTPStatus
from django.test import TestCase, Client

from posts.models import User


class PostURLTests(TestCase):

    def setUp(self):
        '''Создаем пользователя и авторизовываем его'''
        self.user = User.objects.create_user(username='user')
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_urls_exist_at_desired_location_for_client(self):
        '''Страницы доступны неавторизованным пользователям'''
        urls_guest_client_status_code = {
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/signup/': HTTPStatus.OK,
        }
        for addres, status in urls_guest_client_status_code.items():
            with self.subTest(addres=addres):
                response = self.client.get(addres)
                self.assertEqual(response.status_code, status)

    def test_urls_exist_at_desired_location_for_users(self):
        '''Страницы доступны авторизованным пользователям'''
        urls_user_client_status_code = {
            '/auth/password_change/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
        }
        for address, status in urls_user_client_status_code.items():
            with self.subTest(address=address):
                response = self.user_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_password_change_url_redirect_guest_clients_on_login(self):
        '''Перенаправление гостевого пользователя на страцицу авторизации'''
        response = self.client.get('/auth/password_change/')
        self.assertRedirects(
            response, '/auth/login/?next=/auth/password_change/'
        )

    def test_urls_uses_correct_template(self):
        '''URL адрес использует соответсвующий шаблон'''
        urls_templates_names = {
            '/auth/login/': 'users/login.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/logout/': 'users/logged_out.html',
        }

        for address, template in urls_templates_names.items():
            with self.subTest(address=address):
                response = self.user_client.get(address)
                self.assertTemplateUsed(response, template)
