from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea, label='Содержание поста')

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
