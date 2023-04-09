from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
# from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_paginator_func


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.author:
        comment.delete()
    return redirect('posts:post_detail', post_id=comment.post.id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related('group', 'author').all()
    follow_posts = posts.filter(author__following__user=request.user)
    page_obj = get_paginator_func(request, follow_posts)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = True if Follow.objects.filter(
        user=request.user, author=author
    ) else False
    if author != request.user and not following:
        Follow.objects.get_or_create(
            author=author,
            user=request.user
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    if username != request.user:
        get_object_or_404(Follow.objects.filter(
            author__username=username
        )).delete()
    return redirect('posts:profile', username)


# @cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author').all()
    page_obj = get_paginator_func(request, posts)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


@login_required
def post_create(request):
    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    form.instance.author = request.user
    form.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):

    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        instance=post,
        data=request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    form.save()
    return redirect('posts:post_detail', post.id)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').all()
    page_obj = get_paginator_func(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context, slug)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_follow = author.follower.select_related('user')
    author_following = author.following.select_related('author')

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        )
    posts = author.posts.select_related('group').all()
    page_obj = get_paginator_func(request, posts)
    context = {
        'author': author,
        'following': following,
        'author_following': author_following,
        'user_follow': user_follow,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)
