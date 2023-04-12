from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post
from ..constants import (
    USER_NAME,
    GROUP_TITLE,
    GROUP_DESCRIPTION,
    GROUP_SLUG,
    POST_TEXT,
)

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_NAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        test_post = PostModelTest.post
        self.assertEqual(
            str(test_post),
            test_post.text[:15],
        )

        test_group = PostModelTest.group
        self.assertEqual(str(test_group), test_group.title)
