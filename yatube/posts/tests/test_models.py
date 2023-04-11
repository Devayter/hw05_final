from django.test import TestCase

from posts.models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            description='Тестовое описание',
            slug='Тестовый слаг',
            title='Тестовая группа'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Текст тестового поста'
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def test_post_models_method_str_works_correct(self):
        """Метод __str__ модели Post работает корректно"""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_group_models_method_str_works_correct(self):
        '''Метод __str__ модели Group работает корректно'''
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_comment_models_method_str_works_correct(self):
        '''Метод __str__ модели Comment работает корректно'''
        comment = PostModelTest.comment
        expected_object_name = comment.text[:15]
        self.assertEqual(expected_object_name, str(comment))

    def test_follow_models_method_str_works_correct(self):
        '''Метод __str__ модели Follow работает корректно'''
        follow = PostModelTest.follow
        expected_object_name = (f'пользователь {self.user} подписан на '
                                f'{self.author}')
        self.assertEqual(expected_object_name, str(follow))
