from django.test import TestCase
from ..models import Group, Post, User


class PostGroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slugs',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост текст',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.post = PostGroupModelTest.post
        self.post_str = str(self.post)
        self.assertEqual(len(self.post_str), 15)

        self.group = PostGroupModelTest.group
        self.group_str = str(self.group)
        self.assertEqual((self.group_str), self.group.title)

    def test_post_verbose_name(self):
        """Проверка verbose_name у модели post."""
        data_verboses_names_post = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа', }
        for value, expected in data_verboses_names_post.items():
            with self.subTest(value=value):
                verbose_name = self.post._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_post_help_text(self):
        """Проверка help_text у модели post"""
        data_help_text_post = {
            'text': 'Текст нового поста',
            'group': 'Группа к которой будет относиться пост',
        }
        for value, expected in data_help_text_post.items():
            with self.subTest(value=value):
                help_text = self.post._meta.get_field(value).help_text
                self.assertEqual(help_text, expected)

    def test_group_verbose_name(self):
        """Проверка verbose_name у модели group."""
        data_verboses_names_group = {
            'title': 'Название группы',
            'slug': 'slug Группы',
            'description': 'Описание Группы',
        }
        for value, expected in data_verboses_names_group.items():
            with self.subTest(value=value):
                verbose_name = self.group._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)
