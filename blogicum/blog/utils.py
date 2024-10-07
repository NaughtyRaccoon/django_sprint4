from django.utils import timezone
from django.core.paginator import Paginator

from blog.models import Post


def posts_filter(category=None, include_author_location=False):
    filters = {
        'is_published': True,
        'pub_date__lte': timezone.now(),
        'category__is_published': True
    }
    if category:
        filters['category'] = category

    queryset = Post.objects.filter(**filters)
    if include_author_location:
        queryset = queryset.select_related('author', 'location', 'category')
    else:
        queryset = queryset.select_related('category')

    return queryset


def posts_paginator(request, posts, posts_limit):
    paginator = Paginator(posts, posts_limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
