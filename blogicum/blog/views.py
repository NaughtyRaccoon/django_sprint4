from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.db.models import Count

from blog.models import Category, Post, Comment
from .utils import posts_filter, posts_paginator, timezone
from .forms import PostForm, UserProfileForm, CommentForm


POSTS_LIMIT = 10


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.is_published = form.instance.pub_date <= timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return HttpResponseRedirect(post.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['comments'] = Comment.objects.filter(
            post=self.object.post).order_by('created_at')
        return context


class EditCommentView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment = super().get_object(queryset)
        if comment.author != self.request.user:
            raise PermissionDenied
        return comment

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.object.post_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context


class PostDeleteConfirmView(LoginRequiredMixin, TemplateView):
    template_name = 'blog/create.html'
    model = Post

    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author == request.user:
            post.delete()
            return redirect('blog:index')
        return HttpResponseForbidden()


class CommentDeleteConfirmView(LoginRequiredMixin, TemplateView):
    template_name = 'blog/comment.html'
    model = Comment

    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs['comment_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author == request.user:
            comment.delete()
            return redirect(
                reverse('blog:post_detail', args=[comment.post_id])
            )
        return HttpResponseForbidden()


def index(request):
    post_list = posts_filter().annotate(
        comment_count=Count('comments')).order_by('-pub_date')
    page_obj = posts_paginator(request, post_list, POSTS_LIMIT)
    comment_count = Comment.objects.count()
    comments = Comment.objects.all()
    context = {
        'page_obj': page_obj,
        'comment_count': comment_count,
        'comments': comments
    }
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not post.is_published or not post.category.is_published:
        if post.author != request.user:
            raise Http404
    if post.pub_date > timezone.now() and post.author != request.user:
        raise Http404
    comment_form = CommentForm()
    comment_count = Comment.objects.filter(post=post).count()
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post, 'form': comment_form,
        'comment_count': comment_count, 'comments': comments
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = posts_filter(
        category=category, include_author_location=True
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    page_obj = posts_paginator(request, posts, POSTS_LIMIT)
    comment_count = Comment.objects.filter(post__category=category).count()
    comments = Comment.objects.filter(post__category=category)
    context = {
        'category': category,
        'page_obj': page_obj,
        'comment_count': comment_count, 'comments': comments
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.post_set.all().annotate(
        comment_count=Count('comments')).order_by('-pub_date')
    page_obj = posts_paginator(request, posts, POSTS_LIMIT)
    return render(
        request, 'blog/profile.html', {'profile': user, 'page_obj': page_obj}
    )


@login_required
def edit_profile(request):
    user = request.user
    form = UserProfileForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/user.html', {'form': form})
