from .models import Post, Group
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, User, Group, Follow
from .forms import PostForm, CommentForm
from .utils import paginator


def index(requests):
    template = 'posts/index.html'
    post = Post.objects.select_related('author', 'group')
    page_obj = paginator(request=requests, post=post)
    context = {
        'page_obj': page_obj
    }
    return render(requests, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group')
    page_obj = paginator(request=request, post=posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post = author.posts.select_related('group')
    page_obj = paginator(request=request, post=post)
    posts_count = post.count()
    first_post = post.first()
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user).exists())
    context = {
        'author': author,
        'page_obj': page_obj,
        'first_post': first_post,
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    comment_form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    count = post.author.posts.count()
    comments = post.comments.all()
    context = {
        'count': count,
        'post': post,
        'form': comment_form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
        'is_edit': False}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create.html'
    posts = Post.objects.select_related('group')
    post = get_object_or_404(posts, id=post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if post.author != request.user:
        return redirect('posts:index')
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.select_related(
        'author', 'group').filter(author__following__user=request.user)
    page_obj = paginator(request=request, post=posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_follow = Follow.objects.filter(user=request.user, author=author)
    if author != request.user and not is_follow.exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('posts:profile', username=username)
