from django.forms import ModelForm
from .models import Post, Comment


class PostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['group'].empty_label = None
        self.fields['group'].widget.choices = self.fields['group'].choices

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
