import tempfile
import shutil
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Group, Post, User, Follow

COUNT_POSTS: int = 13
FIRS_PAGE_COUNT_POSTS: int = 10
SECOND_PAGE_COUNT_POSTS: int = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        my_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='my_gif.gif',
            content=my_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        
    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def cheking_post(self, test_post_object):
        with self.subTest(post=test_post_object):
            self.assertEqual(test_post_object.text, self.post.text)
            self.assertEqual(test_post_object.author, self.post.author)
            self.assertEqual(test_post_object.group.id, self.post.group.id)
            self.assertEqual(test_post_object.image, self.post.image)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """View URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ),
            'posts/create.html': reverse('posts:post_create'),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Проверка на то, что шаблон index сформир. с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        test_post_object = response.context['page_obj'][0]
        self.cheking_post(test_post_object=test_post_object)
        self.assertEqual(test_post_object, self.post)

    def test_group_list_page_show_correct_context(self):
        """Проверка на то, что шаблон group_list сф. с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        test_post_object = response.context['page_obj'][0]
        self.cheking_post(test_post_object=test_post_object)
        self.assertEqual(str(test_post_object), str(self.post))

    def test_profile_page_show_correct_context(self):
        """Проверка на то, что шаблон profile сф. с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}))
        self.assertEqual(response.context['author'], self.user)
        test_post_object = response.context['page_obj'][0]
        self.cheking_post(test_post_object=test_post_object)
        self.assertEqual(test_post_object, response.context['first_post'])

    def test_post_detail_page_show_correct_context(self):
        """Проверка на то,чтошаблон post_detail сф. с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}))
        test_post_object = response.context['post']
        self.cheking_post(test_post_object=test_post_object)

    def test_post_edit_page_chow_correct_context(self):
        """Проверка на то, что шаблон post_edit сф. с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        my_is_edit: bool = True
        test_edit = response.context['is_edit']
        self.assertEqual(my_is_edit, test_edit)

    def test_create_page_show_correct_context(self):
        """Проверка на то, что шаблон create сф. с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        my_is_edit: bool = False
        test_edit = response.context['is_edit']
        self.assertEqual(my_is_edit, test_edit)

    def test_check_post_in_group_list_page(self):
        """Проверка на то, что пост отображается на странице группы"""
        post_in_group = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in post_in_group.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_check_post_not_in_any_group_list_page(self):
        """Проверка на то, что пост не поппал в другую группу"""
        post_in_group = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in post_in_group.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        for i in range(COUNT_POSTS):
            Post.objects.create(
                text=f'Пост num{i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.unauthorized_client = Client()
        cache.clear()

    def test_paginator_on_index_grouplist_profile_pages(self):
        """Проверка пагинации на страницах index, group_list, profile"""

        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for reverses in pages:
            with self.subTest(reverses=reverses):
                self.assertEqual(len(self.unauthorized_client.get(
                    reverses).context.get('page_obj')),
                    FIRS_PAGE_COUNT_POSTS
                )
                self.assertEqual(len(self.unauthorized_client.get(
                    reverses + '?page=2').context.get('page_obj')),
                    SECOND_PAGE_COUNT_POSTS)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_cache_work(self):
        """Тестирование работы кеша"""
        new_post = Post.objects.create(
            text='Текст',
            author=self.user,
        )
        # print(Post.objects.all())
        content_after_push = self.guest_client.get(
            reverse('posts:index')).content
        new_post.delete()
        # print(Post.objects.all())
        content_after_delete = self.guest_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_after_push, content_after_delete)


class FollowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.author,
        )

    def setUp(self):
        cache.clear()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)

    def test_follow_on_author(self):
        """Тест подписки на автора"""
        count_followers = Follow.objects.count()
        self.authorized_follower.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        last_follower = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_followers + 1)
        self.assertEqual(last_follower.user_id, self.follower.id)
        self.assertEqual(last_follower.author_id, self.author.id)

    def test_unfollow_author(self):
        """Тест отписки от автора"""

        Follow.objects.create(
            author=self.author,
            user=self.follower,
        )
        count_followers_after_follow = Follow.objects.count()
        self.authorized_follower.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        count_followers_after_unfollow = Follow.objects.count()
        self.assertEqual(
            count_followers_after_unfollow,
            count_followers_after_follow - 1
        )

    def test_check_index_page_follower(self):
        """Проверка, что посты появляются в ленте подписок"""
        Follow.objects.create(
            author=self.author,
            user=self.follower,
        )
        response = self.authorized_follower.get(reverse('posts:follow_index'))
        test_post_object = response.context['page_obj'][0]
        with self.subTest(post=test_post_object):
            self.assertEqual(test_post_object.text, self.post.text)
            self.assertEqual(test_post_object.author, self.post.author)

        # Новая запись не появляется в ленте тех, кто не подписан
        response = self.authorized_author.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
