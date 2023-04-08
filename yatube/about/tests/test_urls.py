from http import HTTPStatus
from django.test import TestCase


class AboutURLTests(TestCase):

    def test_urls_exist_at_desired_location_for_guest_client(self):
        '''Страницы доступны для неавторизованных пользователей'''
        urls_guest_client_status_code = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for addres, status in urls_guest_client_status_code.items():
            with self.subTest(addres=addres):
                response = self.client.get(addres)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_correct_template(self):
        '''URL адрес использует соответсвующий шаблон'''
        urls_templates_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

        for address, template in urls_templates_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)
