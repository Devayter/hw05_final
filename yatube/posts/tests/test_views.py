from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User


class PostViewsTests(TestCase):
    '''Тест View приложения posts'''
    @classmethod
    def setUpClass(cls):
        '''Создаем пользователей, картинку и тестовый пост'''
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='user')
        cls.user_follower = User.objects.create_user(username='follower')
        cls.author_following = User.objects.create_user(username='following')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user
        )

    def setUp(self):
        '''Создаем авторизованный клиент'''
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.user_follower_client = Client()
        self.user_follower_client.force_login(self.user_follower)

    def check_context(self, response, bool=False):
        '''Функция для использования в тестах для проверки переданных в
        контексте автора, группу, текст и дату публикации поста.
        '''
        if not bool:
            view_context = response.context['page_obj'][0]
        else:
            view_context = response.context['post']
        self.assertEqual(view_context.author, self.post.author)
        self.assertEqual(view_context.group, self.post.group)
        self.assertEqual(view_context.text, self.post.text)
        self.assertEqual(view_context.pub_date, self.post.pub_date)
        self.assertEqual(view_context.image, self.post.image)

    def test_index_show_correct_context(self):
        '''Главная страница сформирована с правильным контекстом и отображает
        список постов.
        '''
        response = self.user_client.get(reverse('posts:index'))
        PostViewsTests.check_context(self, response)

    def test_group_list_page_show_correct_context(self):
        '''Страница с постами группы сформирована с правильным контекстом
        и отображает список постов, отфильтрованных по группе.
        '''
        response = self.client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        PostViewsTests.check_context(self, response)
        group_context = response.context['group']
        self.assertEqual(group_context, self.group)

    def test_profile_page_show_correct_context(self):
        '''Страница пользователя сформирована с правильным контекстом
        и отображает список постов, отфильтрованных по автору.
        '''
        response = self.user_client.get(
            reverse('posts:profile', args=(self.user.username,))
        )
        PostViewsTests.check_context(self, response)
        author_context = response.context['author']
        self.assertEqual(author_context, self.post.author)

    def test_post_detail_page_show_correct_context(self):
        '''Страница с подробной информацие о посте сформирована с правильным
        контекстом и отображает пост, отфильтрованный по id.
        '''
        response = self.user_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        PostViewsTests.check_context(self, response, True)
        comment_context_object = response.context['comments'][0]
        self.assertEqual(comment_context_object.text, self.comment.text)

    def test_edit_post_page_show_correct_context(self):
        '''Страницы редактирования и создания поста сформированы с правильным
        контекстом, а при редактировании выводится пост, отфильтрованный по id.
        '''
        urls_reverse_tuple = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.models.ModelChoiceField)
        )
        for address, args in urls_reverse_tuple:
            with self.subTest(address=reverse(address, args=args)):
                response = self.user_client.get(reverse(address, args=args))
                post_context = response.context['form']
                self.assertIsInstance(post_context, PostForm)
                for value, expected in form_fields:
                    with self.subTest():
                        form_field = response.context.get(
                            'form'
                        ).fields.get(value)
                        self.assertIsInstance(form_field, expected)
        self.assertEqual(post_context.instance.id, self.post.id)

    def test_post_in_group(self):
        '''Проверка того, что пост не попал не в ту группу'''
        self.group_new = Group.objects.create(
            title='Группа без постов',
            slug='test_group_new_slug',
            description='Описание пустой группы',
        )
        response = self.user_client.get(
            reverse('posts:group_list', args=(self.group_new.slug,))
        )
        post_in_group_new = response.context['page_obj'].object_list
        self.assertNotIn(self.post, post_in_group_new)
        self.assertIsNotNone(self.post.group)
        response = self.user_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        post_in_old_group = response.context['page_obj'].object_list
        self.assertIn(self.post, post_in_old_group)

    def test_cache_works_correct(self):
        response_before_delete = self.client.get(reverse('posts:index'))
        Post.objects.all().delete
        response_after_delete = self.client.get(reverse('posts:index'))
        self.assertEqual(
            response_before_delete.content,
            response_after_delete.content
        )
        cache.clear()
        response_after_cache_cleared = self.client.get(reverse('posts:index'))
        self.assertNotEqual(
            response_before_delete,
            response_after_cache_cleared
        )

    def test_followers_follow_index_contains_following_posts(self):
        '''Новая записть автора появляется в ленте тех, кто на него
        подписан.
        '''
        response = self.user_follower_client.get(reverse('posts:follow_index'))
        PostViewsTests.check_context(self, response)

    def test_not_followers_follow_index_doesnt_contain_following_posts(self):
        '''Новая записть автора не появляется в ленте тех, кто на него
        не подписан.
        '''
        response = self.user_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj'].object_list), 0)


class PaginatorViewTest(TestCase):
    '''Тест Paginator'''
    AMOUNT_OF_POSTS = 15

    @classmethod
    def setUpClass(cls):
        '''Создается пользователь, группа и 15 постов для тестирования
        корректной работы Paginator.
        '''
        super().setUpClass()
        cls.user_paginator = (
            User.objects.create_user(username='user_paginator')
        )
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_follower_client = Client()
        cls.user_follower_client.force_login(cls.user_follower)
        cls.group_paginator = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user_paginator
        )
        posts_for_paginator_test = [
            Post(
                author=cls.user_paginator,
                group=cls.group_paginator,
                text=f'Тестовый пост Paginator № {post_number}',
            ) for post_number in range(cls.AMOUNT_OF_POSTS)
        ]
        Post.objects.bulk_create(posts_for_paginator_test)

        cls.REVERSE_PAGES_NAMES_LIST_PAGINATOR = (
            ('posts:index', None),
            ('posts:follow_index', None),
            ('posts:group_list', (cls.group_paginator.slug,)),
            ('posts:profile', (cls.user_paginator.username,)),
        )

        cls.AMOUNT_OF_POSTS_PER_PAGE = (
            ('?page=1', settings.POSTS_LIMIT),
            ('?page=2', cls.AMOUNT_OF_POSTS - settings.POSTS_LIMIT)
        )

    def test_first_page_contains_ten_records(self):
        '''На первых страницах index, group_list и profile выводятся 10
        постов.
        '''
        for address, args in self.REVERSE_PAGES_NAMES_LIST_PAGINATOR:
            with self.subTest(address=reverse(address, args=args)):
                for page, amount in self.AMOUNT_OF_POSTS_PER_PAGE:
                    with self.subTest(page):
                        response = self.user_follower_client.get(
                            reverse(address, args=args) + page
                        )
                        self.assertEqual(
                            len(response.context['page_obj'].object_list),
                            amount
                        )
