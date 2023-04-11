from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        '''Создаются неавторизованный пользователь, авторизованный,
        автор поста и тестовый пост.
        '''
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.author_following = User.objects.create_user(username='following')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
        )

        cls.reverse_names_tuple = (
            ('posts:add_comment', (cls.post.id,)),
            ('posts:index', None),
            ('posts:follow_index', None),
            ('posts:profile_follow', (cls.author_following,)),
            ('posts:profile_unfollow', (cls.author_following,)),
            ('posts:group_list', (cls.group.slug,)),
            ('posts:post_create', None),
            ('posts:profile', (cls.user,)),
            ('posts:post_edit', (cls.post.id,)),
            ('posts:post_detail', (cls.post.id,))
        )

        cls.post_edit_add_comment_list = [
            'posts:add_comment',
            'posts:post_edit'
        ]
        cls.follow_list = [
            'posts:profile_follow',
            'posts:profile_unfollow'
        ]

    def setUp(self):
        '''Создаем клиент для пользователя и автора и авторизовываем их'''
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_use_correct_reverse_names(self):
        '''Url адреса равны адресам, полученным через reverse'''
        reverse_names_urls_tuple = (
            ('posts:index', None, '/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_follow',
             (self.author_following,),
             f'/profile/{self.author_following}/follow/'),
            ('posts:profile_unfollow',
             (self.author_following,),
             f'/profile/{self.author_following}/unfollow/'),
            ('posts:add_comment',
             (self.post.id,),
             f'/posts/{self.post.id}/comment/'
             ),
            ('posts:group_list',
             (self.group.slug,),
             f'/group/{self.group.slug}/'
             ),
            ('posts:post_create', None, '/create/'),
            ('posts:profile',
             (self.author,),
             f'/profile/{self.post.author}/',
             ),
            ('posts:post_edit',
             (self.post.id,),
             f'/posts/{self.post.id}/edit/'
             ),
            ('posts:post_detail', (self.post.id,), f'/posts/{self.post.id}/')
        )

        for name, args, url in reverse_names_urls_tuple:
            with self.subTest(address=reverse(name, args=args)):
                self.assertEqual(reverse(name, args=args), url)

    def test_urls_exist_at_desired_location_for_author(self):
        '''Для автора доступны все страницы. После Добавления комментария
        происходит переадресация на подробную информацию о посте. После
        подписки и отписки происходит переадресация на страницу профиля (по
        факту пользователь остается на той же странице). При повторной отписке
        или попытке отписаться при отсутствующей подписке произойдет
        переадресация на страницу 404.
        '''
        for name, args in self.reverse_names_tuple:
            with self.subTest(address=reverse(name, args=args)):
                if name == 'posts:profile_follow':
                    response = self.author_client.get(
                        reverse(name, args=args),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:profile', args=args)
                    )
                elif name == 'posts:profile_unfollow':
                    response = self.author_client.get(
                        reverse(name, args=args),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:profile', args=args)
                    )
                    Follow.objects.all().delete()
                    response = self.author_client.get(
                        reverse(name, args=args),
                        follow=True
                    )
                    self.assertEqual(
                        response.status_code, HTTPStatus.NOT_FOUND
                    )
                elif name == 'posts:add_comment':
                    response = self.author_client.get(
                        reverse(name, args=args),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:post_detail', args=args)
                    )
                else:
                    response = self.author_client.get(reverse(name, args=args))

                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exist_at_desired_location_for_user(self):
        '''Для пользователя доступны все страницы, кроме post_edit.
        Со страницы post_edit происходит redirect на post_detail. После
        Добавления комментария, подписки и отписки происходит переадресация на
        профиль и на подробную информацию о посте(по факту пользователь
        остается на той же странице).
        '''
        for name, args in self.reverse_names_tuple:
            with self.subTest(address=reverse(name, args=args)):
                if name in self.follow_list:
                    response = self.user_client.get(
                        reverse(name, args=args),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:profile', args=args)
                    )
                elif name in self.post_edit_add_comment_list:
                    response = self.user_client.get(
                        reverse(name, args=args),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:post_detail', args=args)
                    )
                else:
                    response = self.user_client.get(reverse(name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exist_at_desired_location_for_guest_user(self):
        '''Для неавторизованного пользователя доступны все страницы, кроме
        post_edit, post_create и follow-index. Со страницы post_edit происходит
        redirect на post_detail, а с post_create, follow_index, add_coment
        profile_follow и profile_unfollow на сраницу авторизации.
        '''
        names_list = [
            'posts:add_comment',
            'posts:follow_index',
            'posts:profile_follow',
            'posts:profile_unfollow',
            'posts:post_edit',
            'posts:post_create',
        ]
        for name, args in self.reverse_names_tuple:
            with self.subTest(address=reverse(name, args=args)):
                if name in names_list:
                    response = self.client.get(
                        reverse(name, args=args),
                        follow=True
                    )
                    log_in = reverse('users:login') + '?next='
                    reverse_name = reverse(name, args=args)
                    self.assertRedirects(
                        response,
                        f'{log_in}{reverse_name}'
                    )
                else:
                    response = self.client.get(reverse(name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_unexiting_page_status_code_and_correcr_teplate(self):
        '''Несуществующая страница использует соответствуюший шаблон и вернет
        ошибку 404.
        '''
        response = self.client.get('/unexisting_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_use_correct_template(self):
        '''URL адрес использует соответсвующий шаблон'''
        urls_templates_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:post_create', None, 'posts/post_create.html'),
            ('posts:profile', (self.user,), 'posts/profile.html',),
            ('posts:post_edit', (self.post.id,), 'posts/post_create.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
        )
        for name, args, templates in urls_templates_names:
            with self.subTest(address=reverse(name, args=args)):
                response = self.author_client.get(reverse(name, args=args))
                self.assertTemplateUsed(response, templates)
