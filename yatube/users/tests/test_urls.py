from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client
from .constants import (
    USER_NAME,
    USERS_SINGUP_URL_NAME,
    USERS_LOGOUT_URL_NAME,
    USERS_LOGIN_URL_NAME,
    USERS_PWD_CH_URL_NAME,
    USERS_PWD_CH_D_URL_NAME,
    USERS_PWD_RST_URL_NAME,
    USERS_PWD_RST_D_URL_NAME,
    USERS_PWD_RST_CFRM_URL_NAME,
    USERS_PWD_RST_CMPLT_URL_NAME,
    USERS_SINGUP_TEMPLATE,
    USERS_LOGOUT_TEMPLATE,
    USERS_LOGIN_TEMPLATE,
    USERS_PWD_CH_TEMPLATE,
    USERS_PWD_CH_D_TEMPLATE,
    USERS_PWD_RST_TEMPLATE,
    USERS_PWD_RST_D_TEMPLATE,
    USERS_PWD_RST_CFRM_TEMPLATE,
    USERS_PWD_RST_CMPLT_TEMPLATE,
)
from http import HTTPStatus

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_NAME)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_urls_available_and_uses_correct_template(self):
        """Проверка доступности страниц и используемых шаблонов"""
        data = {
            USERS_SINGUP_URL_NAME: (
                USERS_SINGUP_TEMPLATE,
                {},
                self.client,
                '',
            ),
            USERS_LOGIN_URL_NAME: (
                USERS_LOGIN_TEMPLATE,
                {},
                self.client,
                '',
            ),
            USERS_PWD_CH_URL_NAME: (
                USERS_PWD_CH_TEMPLATE,
                {},
                self.authorized_client,
                USERS_LOGIN_URL_NAME,
            ),
            USERS_PWD_CH_D_URL_NAME: (
                USERS_PWD_CH_D_TEMPLATE,
                {},
                self.authorized_client,
                USERS_LOGIN_URL_NAME,
            ),
            USERS_PWD_RST_URL_NAME: (
                USERS_PWD_RST_TEMPLATE,
                {},
                self.client,
                '',
            ),
            USERS_PWD_RST_D_URL_NAME: (
                USERS_PWD_RST_D_TEMPLATE,
                {},
                self.client,
                '',
            ),
            USERS_PWD_RST_CFRM_URL_NAME: (
                USERS_PWD_RST_CFRM_TEMPLATE,
                {'uidb64': 'uidb64',
                 'token': 'token'},
                self.client,
                '',
            ),
            USERS_PWD_RST_CMPLT_URL_NAME: (
                USERS_PWD_RST_CMPLT_TEMPLATE,
                {},
                self.client,
                '',
            ),
            USERS_LOGOUT_URL_NAME: (
                USERS_LOGOUT_TEMPLATE,
                {},
                self.authorized_client,
                '',
            ),
        }
        for url_name, params in data.items():
            with self.subTest(url_name=url_name):
                template, kwargs, client, redirect_url = params
                response = client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
                if client == self.authorized_client and redirect_url:
                    response = self.client.get(
                        reverse(url_name, kwargs=kwargs)
                    )
                    self.assertRedirects(
                        response,
                        f'{reverse(redirect_url)}?next='
                        f'{reverse(url_name, kwargs=kwargs)}'
                    )
