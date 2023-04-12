from http import HTTPStatus

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client

from posts.models import Group, Post
from ..constants import (
    USER_NAME,
    GROUP_TITLE,
    GROUP_SLUG,
    GROUP_DESCRIPTION,
    POST_TEXT,
    INDEX_URL_NAME,
    GROUP_LIST_URL_NAME,
    PROFILE_URL_NAME,
    POST_CREATE_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_DETAIL_URL_NAME,
    USERS_LOGIN_URL_NAME,
    INDEX_TEMPLATE,
    GROUP_LIST_TEMPLATE,
    PROFILE_TEMPLATE,
    POST_CREATE_TEMPLATE,
    POST_EDIT_TEMPLATE,
    POST_DETAIL_TEMPLATE,
    TEMPLATE_404,
)

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_NAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_urls_available_and_uses_correct_template(self):
        """Проверка доступности страниц и используемых шаблонов"""
        data = {
            INDEX_URL_NAME: (
                INDEX_TEMPLATE,
                {},
                self.client,
                '',
            ),
            GROUP_LIST_URL_NAME: (
                GROUP_LIST_TEMPLATE,
                {'slug': self.group.slug},
                self.client,
                '',
            ),
            PROFILE_URL_NAME: (
                PROFILE_TEMPLATE,
                {'username': self.user.username},
                self.client,
                '',
            ),
            POST_CREATE_URL_NAME: (
                POST_CREATE_TEMPLATE,
                {},
                self.authorized_client,
                USERS_LOGIN_URL_NAME,
            ),
            POST_EDIT_URL_NAME: (
                POST_EDIT_TEMPLATE,
                {'post_id': self.post.id},
                self.authorized_client,
                USERS_LOGIN_URL_NAME,
            ),
            POST_DETAIL_URL_NAME: (
                POST_DETAIL_TEMPLATE,
                {'post_id': self.post.id},
                self.client,
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
                        '{redirect_url}?next={url}'.format(
                            redirect_url=reverse(redirect_url),
                            url=reverse(url_name, kwargs=kwargs)
                        )
                    )

    def test_unexiting_page(self):
        """Проверка несуществующей страницы"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, TEMPLATE_404)
