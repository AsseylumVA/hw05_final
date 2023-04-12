from django.urls import reverse
from django.test import TestCase
from http import HTTPStatus


class StaticURLTests(TestCase):

    def test_urls_available_and_uses_correct_template(self):
        data = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }

        for url_name, template in data.items():
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
