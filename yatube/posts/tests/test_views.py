import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.paginator import Page
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import (
    Client,
    TestCase,
)
from django.urls import reverse

from ..models import (
    Group,
    Post,
    User,
    Follow,
)
from posts.forms import PostForm

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
    FOLLOW_URL_NAME,
    UNFOLLOW_URL_NAME,
)
from yatube.settings import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class ViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USER_NAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )

        Post.objects.bulk_create(
            [
                Post(
                    text=f'{POST_TEXT}{i}',
                    author=cls.author,
                    group=cls.group,
                ) for i in range(POSTS_PER_PAGE + 5)
            ]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.author)

    def tearDown(self):
        cache.clear()

    def test_paginator(self):
        """Проверка паджинатора"""

        data = {
            INDEX_URL_NAME: (
                {},
                Post.objects.all()[:POSTS_PER_PAGE],
            ),
            GROUP_LIST_URL_NAME: (
                {'slug': self.group.slug},
                self.group.posts.all()[:POSTS_PER_PAGE],
            ),
            PROFILE_URL_NAME: (
                {'username': self.author.username},
                self.author.posts.all()[:POSTS_PER_PAGE],
            ),
        }

        for url_name, params in data.items():
            with self.subTest(url_name=url_name):
                kwargs, posts = params
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj,
                    posts,
                    transform=lambda x: x
                )

    def test_context_posts_pages(self):
        """Проверка контекста"""
        post = Post.objects.get(id=1)
        data = {
            POST_CREATE_URL_NAME: (
                {},
                {'form': PostForm}
            ),
            POST_EDIT_URL_NAME: (
                {'post_id': post.id},
                {'form': PostForm}
            ),
            POST_DETAIL_URL_NAME: (
                {'post_id': post.id},
                {'post': Post}
            ),
        }

        for url_name, params in data.items():
            with self.subTest(url_name=url_name):
                kwargs, context = params
                response = self.auth_client.get(
                    reverse(url_name, kwargs=kwargs)
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                for field, expected in context.items():
                    request_field = response.context.get(field)
                    self.assertIsNotNone(request_field)
                    self.assertIsInstance(request_field, expected)

    def test_post_create_view(self):
        """
        Проверка правильного отображения созданного поста на страницах
        index, group_list, profile
        А так же проверка, что пост не отображается в group_list другой группы
        """
        new_post = Post.objects.create(
            text=POST_TEXT,
            author=self.author,
            group=self.group,
        )
        new_group = Group.objects.create(
            title=GROUP_TITLE,
            slug=f'{GROUP_SLUG}_new',
            description=GROUP_DESCRIPTION,
        )
        data = {
            INDEX_URL_NAME: {},
            GROUP_LIST_URL_NAME: {
                'slug': self.group.slug
            },
            PROFILE_URL_NAME: {
                'username': self.author.username
            },
        }

        for url_name, kwargs in data.items():
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)

                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertIn(new_post, page_obj)

        # Тест - Пост не попадает на страницу другой группы
        response = self.client.get(
            reverse(GROUP_LIST_URL_NAME, kwargs={'slug': new_group.slug})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        page_obj = response.context.get('page_obj')
        self.assertIsNotNone(page_obj)
        self.assertIsInstance(page_obj, Page)
        self.assertNotIn(new_post, page_obj)

    def test_images_in_context(self):
        """Тест постов с картинками на разных страницах"""

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        new_post = Post.objects.create(
            text=POST_TEXT,
            author=self.author,
            group=self.group,
            image=uploaded,
        )

        data = {
            INDEX_URL_NAME: {},
            PROFILE_URL_NAME: {
                'username': self.author.username
            },
            GROUP_LIST_URL_NAME: {
                'slug': self.group.slug
            },
        }
        for url_name, kwargs in data.items():
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)

                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)

                post = page_obj[0]
                self.assertIsNotNone(post)
                self.assertIsInstance(post, Post)
                self.assertEqual(post, new_post)
                self.assertEqual(post.image, new_post.image)

        response = self.client.get(
            reverse(
                POST_DETAIL_URL_NAME,
                kwargs={'post_id': new_post.id}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        post = response.context.get('post')
        self.assertEqual(post.image, new_post.image)

    def test_cache_index_page(self):
        """Тест кеширования главной страницы"""
        response = self.client.get(reverse(INDEX_URL_NAME))
        content = response.content

        Post.objects.all().delete()

        # Получаем кешированный контент
        response = self.client.get(reverse(INDEX_URL_NAME))
        self.assertEqual(content, response.content)

        cache.clear()

        # Получаем новый контент
        response = self.client.get(reverse(INDEX_URL_NAME))
        self.assertNotEqual(content, response.content)

    def test_follows(self):
        """Тест подписок"""
        follow_author = User.objects.create_user(username='author')
        author_name = follow_author.username
        response = self.auth_client.get(
            reverse(FOLLOW_URL_NAME, kwargs={'username': author_name})
        )
        self.assertRedirects(
            response,
            reverse(
                PROFILE_URL_NAME,
                kwargs={'username': author_name},
            ),
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.author,
                author=follow_author,
            ).exists()
        )

        response = self.auth_client.get(
            reverse(UNFOLLOW_URL_NAME, kwargs={'username': author_name})
        )
        self.assertRedirects(response, reverse(
            PROFILE_URL_NAME,
            kwargs={'username': author_name},
        ))
        self.assertFalse(
            Follow.objects.filter(user=self.author,
                                  author=follow_author,).exists()
        )
