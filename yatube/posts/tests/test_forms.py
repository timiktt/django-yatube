import tempfile
import shutil
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core.cache import cache
from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_posts_forms_create_post(self):
        """Проверка, создает ли форма пост c картинкой в базе."""
        post_count = Post.objects.count()
        my_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='my_gif.gif',
            content=my_gif,
            content_type='image/gif'
        )
        data_post = {
            'text': 'Текст нового поста',
            'group': self.group.id,
            'image': image,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=data_post,
        )

        last_post = Post.objects.last()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(last_post.text, data_post['text'])
        self.assertEqual(last_post.group.id, data_post['group'])
        self.assertEqual(last_post.image.name, 'posts/my_gif.gif')

    def test_posts_forms_edit_post(self):
        """Проверка, редактируется ли пост."""

        data_post = {
            'text': 'Текст нового поста',
            'group': self.group.id,
        }
        data_edit_post = {
            'text': 'Текст изм. поста',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=data_post,
        )
        post_count = Post.objects.count()
        post_id = Post.objects.last().id

        self.authorized_client.post(reverse(
            'posts:post_edit',
            kwargs={'post_id': post_id},
        ), data=data_edit_post)

        post = Post.objects.get(id=post_id)
        self.assertEqual(post_count, Post.objects.count())
        self.assertEqual(post.text, data_edit_post['text'])
        self.assertEqual(post.group.id, data_edit_post['group'])

    def test_authorized_user_can_add_comment(self):
        """Проверка, что авт.пользователь может добавить комментарий"""

        comment_count = Comment.objects.count()
        data_post = {
            'text': 'Текст нового поста',
            'group': self.group.id,
        }
        data_comment = {
            'text': 'Текст нового комментария'
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=data_post,
        )
        post_id = Post.objects.last().id
        # print(post_id)
        comment = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post_id}
            ),
            data=data_comment,
        )
        comment_on_page = reverse('posts:post_detail', args={post_id})
        last_comment = Comment.objects.last()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(last_comment.text, data_comment['text'])
        self.assertEqual(last_comment.author, self.user)
        self.assertEqual(last_comment.post_id, post_id)
        self.assertRedirects(comment, comment_on_page)
