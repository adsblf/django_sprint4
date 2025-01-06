from datetime import datetime

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseServerError
from django.db import DatabaseError

from .forms import PostForm, CommentForm, UserForm
from .models import Post, Category, User, Comment


NUMBER_OF_PAGINATOR_PAGES = 10


def get_posts(**kwargs):
    """Отфильтрованное получение постов"""
    try:
        return Post.objects.select_related(
            'category',
            'location',
            'author'
        ).annotate(comment_count=Count('comments')
                   ).filter(**kwargs).order_by('-pub_date')
    except DatabaseError:
        raise HttpResponseServerError("Ошибка при получении сообщений.")


def get_paginator(request, queryset,
                  number_of_pages=NUMBER_OF_PAGINATOR_PAGES):
    """
    Представление queryset в виде пагинатора,
    по N-шт на странице
    """
    paginator = Paginator(queryset, number_of_pages)
    page_number = request.GET.get('page')
    try:
        return paginator.get_page(page_number)
    except (ValueError, TypeError):
        return paginator.get_page(1)


def index(request):
    """Главная страница / Лента публикаций"""
    try:
        posts = get_posts(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now())
        page_obj = get_paginator(request, posts)
    except Http404:
        page_obj = None
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def category_posts(request, category_slug):
    """Отображение публикаций в категории"""
    try:
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True)
        posts = get_posts(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now(),
            category=category)
        page_obj = get_paginator(request, posts)
    except Http404:
        page_obj = None
    context = {'category': category,
               'page_obj': page_obj}
    return render(request, 'blog/post_list.html', context)


def post_detail(request, post_id):
    """Отображение полного описания выбранной публикации"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        post = get_object_or_404(
            Post,
            id=post_id,
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now())
    form = CommentForm(request.POST or None)
    try:
        comments = Comment.objects.select_related(
            'author').filter(post=post)
    except DatabaseError:
        comments = []
    context = {'post': post,
               'form': form,
               'comments': comments}
    return render(request, 'blog/post_detail.html', context)


@login_required
def create_post(request):
    """Создание публикации"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        try:
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', request.user)
        except DatabaseError:
            return HttpResponseServerError("Ошибка при сохранении записи.")
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def edit_post(request, post_id):
    """Редактирование публикации"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        try:
            form.save()
            return redirect('blog:post_detail', post_id)
        except DatabaseError:
            return HttpResponseServerError("Ошибка при обновлении записи.")
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def delete_post(request, post_id):
    """Удаление публикации"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST':
        try:
            post.delete()
            return redirect('blog:index')
        except DatabaseError:
            return HttpResponseServerError("Ошибка при удалении записи.")
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к публикации"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        try:
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
        except DatabaseError:
            return HttpResponseServerError("Ошибка при добавлении комментария")
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария к публикации"""
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        try:
            form.save()
            return redirect('blog:post_detail', post_id)
        except DatabaseError:
            return HttpResponseServerError("Ошибка при обновлении комментария")
    context = {'comment': comment,
               'form': form}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария к публикации"""
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        try:
            comment.delete()
            return redirect('blog:post_detail', post_id)
        except DatabaseError:
            return HttpResponseServerError("Ошибка при удалении комментария.")
    context = {'comment': comment}
    return render(request, 'blog/comment.html', context)


def profile(request, username):
    """Отображение страницы пользователя"""
    profile = get_object_or_404(
        User,
        username=username)
    try:
        posts = get_posts(author=profile)
        if request.user != profile:
            posts = get_posts(
                is_published=True,
                category__is_published=True,
                pub_date__lte=datetime.now(),
                author=profile)
        page_obj = get_paginator(request, posts)
    except Http404:
        page_obj = None
    context = {'profile': profile,
               'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование страницы пользователя"""
    profile = get_object_or_404(
        User,
        username=request.user)
    form = UserForm(request.POST or None, instance=profile)
    if form.is_valid():
        try:
            form.save()
            return redirect('blog:profile', request.user)
        except DatabaseError:
            return HttpResponseServerError("Ошибка при редактировании профиля")
    context = {'form': form}
    return render(request, 'blog/user.html', context)
