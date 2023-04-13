import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    '''Тест forms приложения posts'''
    @classmethod
    def setUpClass(cls):
        '''Создаем пользователей, комментарий и пост'''
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')
        cls.user_follower = User.objects.create_user(username='follower')
        cls.author_following = User.objects.create_user(username='following')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Текст до редактирования',
        )

    @classmethod
    def tearDownClass(cls):
        '''Выполняется по окончанию всех тестов и удаляет временную папку
        вместе с загруженными в нее файлами.
        '''
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        '''Создаем клиент и авторизовываем автора и пользователя'''
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.user_follower_client = Client()
        self.user_follower_client.force_login(self.user_follower)

    def test_post_create_form_add_new_post(self):
        '''При отправке валидной формы со страницы создания поста добавляется
        новая запись в базу данных.
        '''
        Post.objects.all().delete()
        post_create_test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='post_create_test_image.gif',
            content=post_create_test_image,
            content_type='image/gif'
        )
        post_create_form_data = {
            'group': self.group.id,
            'text': 'Текст нового поста',
            'image': uploaded
        }
        posts_count_before_post_request = Post.objects.count()
        self.author_client.post(
            reverse('posts:post_create'),
            data=post_create_form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count_before_post_request + 1
        )
        post_created = Post.objects.first()
        self.assertEqual(post_created.author, self.post.author)
        self.assertEqual(post_created.group.id, post_create_form_data['group'])
        self.assertEqual(post_created.text, post_create_form_data['text'])
        self.assertEqual(
            post_created.image.name,
            f'posts/{uploaded.name}'
        )

    def test_post_edit_form_change_post(self):
        '''При отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных.
        '''
        new_group = Group.objects.create(
            title='Новая группа',
            slug='test_slug_new',
            description='Описание новой группы',
        )
        post_edit_test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='post_edit_test_image.gif',
            content=post_edit_test_image,
            content_type='image/gif'
        )
        post_edit_form_data = {
            'group': new_group.id,
            'text': 'Текст отредактированного поста',
            'image': uploaded
        }
        posts_count_before_post_edit = Post.objects.count()
        self.author_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=post_edit_form_data,
            follow=True
        )
        self.assertEqual(posts_count_before_post_edit, Post.objects.count())
        response = self.client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_in_old_group = response.context['page_obj']
        self.assertNotIn(self.post, post_in_old_group)
        edited_post = Post.objects.first()
        self.assertEqual(edited_post.author, self.post.author)
        self.assertEqual(edited_post.group.id, post_edit_form_data['group'])
        self.assertEqual(edited_post.text, post_edit_form_data['text'])
        self.assertEqual(edited_post.id, self.post.id)
        self.assertEqual(
            edited_post.image.name,
            f'posts/{uploaded.name}'
        )

    def test_guest_is_not_able_to_create_new_post(self):
        '''У гостевого пользователя нет возможности создавать новые посты'''
        guest_user_post_create_form_data = {
            'group': self.group.id,
            'text': 'Текст создания тестового поста',
        }
        Post.objects.all().delete()
        posts_count_before_create_post = Post.objects.count()
        self.client.post(
            reverse('posts:post_create'),
            data=guest_user_post_create_form_data,
            follow=True
        )
        posts_count_after_post_created = Post.objects.count()
        self.assertEqual(
            posts_count_before_create_post,
            posts_count_after_post_created
        )

    def test_add_comment_form_add_new_comment_on_post_detail(self):
        '''Форма добавления комментария добавляет его на страницу с информацией
        о посте.
        '''
        Comment.objects.all().delete()
        comments_count_before_add_comment = Comment.objects.count()
        comment_form_data = {'text': 'Коментарий авторизованного пользователя'}
        self.user_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=comment_form_data
        )
        self.assertEqual(
            Comment.objects.count(),
            comments_count_before_add_comment + 1
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, comment_form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_guest_user_is_not_able_to_add_new_comment(self):
        '''Гостевого пользователя не способен добавлять новые комментарии'''
        Comment.objects.all().delete()
        comments_count_before_add_comment = Comment.objects.count()
        self.client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data={'text': 'Комментарий неавторизованного пользователя'}
        )
        self.assertEqual(
            Comment.objects.count(),
            comments_count_before_add_comment
        )

    def test_delete_comment_button_works_correct(self):
        '''Кнопка удаление комментариев работает корректно'''
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Комментария для удаления'
        )
        comments_count_before_delete_comment = Comment.objects.count()
        self.user_client.get(
            reverse('posts:delete_comment', args=(comment.id,))
        )
        self.assertEqual(
            Comment.objects.count(),
            comments_count_before_delete_comment - 1
        )

    def test_post_delete_button_works_correct(self):
        '''Кнопка удаления поста работает корректно'''
        post = Post.objects.create(
            author=self.author,
            text='Пост для удаления'
        )
        posts_count_before_delete = Post.objects.count()
        self.author_client.get(
            reverse('posts:post_delete', args=(post.id,))
        )
        self.assertEqual(Post.objects.count(), posts_count_before_delete - 1)

    def test_follow_for_user_works_correct(self):
        '''Авторизованный пользователь может подписываться на других
        пользователей.
        '''
        Follow.objects.all().delete()
        follow_count_before_follow = Follow.objects.all().count()
        self.user_client.get(
            reverse('posts:profile_follow', args=(self.author_following,))
        )
        follow = Follow.objects.first()
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, self.author_following)
        self.assertEqual(
            Follow.objects.all().count(),
            follow_count_before_follow + 1
        )

    def test_unfollow_for_user_works_correct(self):
        '''Авторизованный пользователь может отписываться от других
        пользователей.
        '''
        Follow.objects.all().delete()
        Follow.objects.create(
            user=self.user_follower,
            author=self.author_following
        )
        follow_count_before_delete = Follow.objects.all().count()
        self.user_follower_client.get(
            reverse('posts:profile_unfollow', args=(self.author_following,)))
        self.assertEqual(
            Follow.objects.all().count(), follow_count_before_delete - 1
        )

    def test_follow_cannot_resubscribe(self):
        '''Отсутствует возможность подписаться повторно'''
        Follow.objects.all().delete()
        self.user_client.get(
            reverse('posts:profile_follow', args=(self.author_following,))
        )
        follow_count_before_second_follow = Follow.objects.all().count()
        self.user_client.get(
            reverse('posts:profile_follow', args=(self.author_following,))
        )
        self.assertEqual(
            follow_count_before_second_follow,
            Follow.objects.all().count()
        )

    def test_follow_author_cannor_follow_himself(self):
        '''Отсутствует возможность автора подписаться на самого себя'''
        Follow.objects.all().delete()
        self.author_client.get(
            reverse('posts:profile_follow', args=(self.author,))
        )
        follow_count_after_follow = Follow.objects.all().count()
        self.assertEqual(follow_count_after_follow, 0)
