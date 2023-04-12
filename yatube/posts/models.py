from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Название сообщества', max_length=200)
    slug = models.SlugField('Идентификатор сообщества в URL', unique=True)
    description = models.TextField('Описание сообщества')

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField('Содержание поста', blank=True, null=True)
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Сообщество для публикации поста',
        help_text='Сообщество, к которому будет относиться пост',
    )

    image = models.ImageField(
        'Изображение',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'Пост (публикация)'
        verbose_name_plural = 'Посты (публикации)'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField('Комментарий', help_text='Текст комментария')
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )
