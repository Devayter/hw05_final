from django.conf import settings
from django.core.paginator import Paginator


def get_paginator_func(request, *args):
    paginator = Paginator(*args, settings.POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
