import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase, Client, override_settings

from posts.models import Post, Group

from ..constants import (
    USER_NAME,
    POST_TEXT,
    PROFILE_URL_NAME,
    POST_CREATE_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_DETAIL_URL_NAME,
    GROUP_TITLE,
    GROUP_DESCRIPTION,
    GROUP_SLUG,
    USERS_LOGIN_URL_NAME,
    COMMENT_ADD_URL_NAME,
)

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class FormsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USER_NAME)
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.author,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_create_post(self):
        """Владиная форма создаст пост"""
        posts_count = Post.objects.count()

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

        form_data = {
            'text': POST_TEXT,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse(POST_CREATE_URL_NAME),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(PROFILE_URL_NAME,
                    kwargs={'username': self.author.username})
        )
        self.assertNotEqual(posts_count, Post.objects.count())

    def test_create_post_invalid_image(self):
        """Проверка с другим файлом вместо картинки"""
        uploaded = SimpleUploadedFile(
            name='small.txt',
            content=b'not image',
            content_type='text/txt'
        )
        form_data = {
            'text': POST_TEXT,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(POST_CREATE_URL_NAME),
            data=form_data,
            follow=True,
        )
        self.assertFormError(
            response,
            'form',
            'image',
            ('Загрузите правильное изображение.'
             ' Файл, который вы загрузили,'
             ' поврежден или не является изображением.')
        )

    def test_post_edit(self):
        """Валидная форма редактирует пост"""
        post_id = self.post.id
        post_before_edit = self.post
        group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )

        form_data = {
            'text': 'New text',
            'group': group.id,
        }

        response = self.authorized_client.post(
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': post_id}),
            form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(POST_DETAIL_URL_NAME, kwargs={'post_id': post_id})
        )

        post_after_edit = Post.objects.get(id=post_id)
        self.assertNotEqual(post_before_edit.text,
                            post_after_edit.text)
        self.assertNotEqual(post_before_edit.group,
                            post_after_edit.group)

    def test_comments_sent(self):
        post_id = self.post.id
        comments_before_add = self.post.comments.count()
        form_data = {
            'text': 'New comment',
        }
        path = reverse(COMMENT_ADD_URL_NAME, kwargs={'post_id': post_id})

        # Проверим редирект для неавторизованного юзера.
        response = self.client.post(path, form_data,)
        self.assertRedirects(
            response,
            '{redirect_url}?next={url}'.format(
                redirect_url=reverse(USERS_LOGIN_URL_NAME),
                url=reverse(COMMENT_ADD_URL_NAME, kwargs={'post_id': post_id})
            )
        )
        self.assertEqual(comments_before_add, self.post.comments.count())

        # Теперь для авторизованного
        response = self.authorized_client.post(path, form_data,)
        self.assertNotEqual(comments_before_add, self.post.comments.count())
