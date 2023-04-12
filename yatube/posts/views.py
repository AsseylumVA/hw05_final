from django.shortcuts import (render,
                              get_object_or_404,
                              redirect,
                              )
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from yatube.settings import POSTS_PER_PAGE

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .constants import (
    INDEX_TEMPLATE,
    GROUP_LIST_TEMPLATE,
    PROFILE_TEMPLATE,
    POST_CREATE_TEMPLATE,
    POST_DETAIL_TEMPLATE,
    PROFILE_URL_NAME,
    POST_DETAIL_URL_NAME,
)


def paginate(request, posts):
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница"""
    title = 'Это главная страница проекта Yatube'
    text = 'Последние обновления на сайте'
    posts = Post.objects.all()
    page_obj = paginate(request, posts)
    context = {
        'title': title,
        'text': text,
        'page_obj': page_obj
    }
    return render(request, INDEX_TEMPLATE, context)


def group_posts(request, slug):
    """Страница группы"""
    group = get_object_or_404(Group, slug=slug)
    description = group.description
    posts = group.posts.all()
    page_obj = paginate(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': group.title,
        'description': description,
    }
    return render(request, GROUP_LIST_TEMPLATE, context)


def profile(request, username):
    """Профиль пользователя"""
    author = User.objects.get(username=username)
    posts = author.posts.all()
    posts_count = posts.count()
    page_obj = paginate(request, posts)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()

    context = {
        'author': author,
        'username': username,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, PROFILE_TEMPLATE, context)


def post_detail(request, post_id):
    """Подробности записи"""
    post = get_object_or_404(Post, id=post_id)
    posts_count = Post.objects.filter(author=post.author).count()
    form = CommentForm()
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': post.comments.all(),
    }
    return render(request, POST_DETAIL_TEMPLATE, context)


@login_required
def post_create(request):
    """Страница создания записи"""
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )
        if form.is_valid():
            form.instance.author = request.user
            form.save()
            return redirect(PROFILE_URL_NAME, username=request.user.username)
        return render(request, POST_CREATE_TEMPLATE, {'form': form})

    form = PostForm()
    groups = Group.objects.all()
    context = {
        'form': form,
        'group': groups,
    }
    return render(request, POST_CREATE_TEMPLATE, context)


@login_required
def post_edit(request, post_id):
    """Страница редактирования записи"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect(POST_DETAIL_URL_NAME, post_id=post.id)

    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect(POST_DETAIL_URL_NAME, post_id=form.instance.id)
        return render(request, POST_CREATE_TEMPLATE, {'form': form})

    form = PostForm(
        files=request.FILES or None,
        instance=post,
    )
    context = {
        'is_edit': True,
        'form': form,
    }
    return render(request, POST_CREATE_TEMPLATE, context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(POST_DETAIL_URL_NAME, post_id=post_id)


@login_required
def follow_index(request):
    # не работает с шаблоном posts/post_list.html
    '''posts = request.user.follower.values_list(
        'author__posts'
    ).order_by('author__posts__pub_date')'''

    author_list = request.user.follower.values('author')
    posts = Post.objects.filter(
        author__in=author_list
    )
    title = 'Подписки'
    text = 'Обновления'
    page_obj = paginate(request, posts)
    context = {
        'title': title,
        'text': text,
        'page_obj': page_obj,
    }
    return render(request, INDEX_TEMPLATE, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect(PROFILE_URL_NAME, username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=user, author=author,)
    follow.delete()
    return redirect(PROFILE_URL_NAME, username=username)
