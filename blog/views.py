from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from .forms import EmailPostForm,CommentForm, SearchForm
from django.views.decorators.http import require_POST
from django.contrib.postgres.search import SearchVector, \
 SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity



@require_POST
def post_comment(request,post_id):
    post = get_object_or_404(Post,id = post_id, status = Post.Status.PUBLISHED)
    comment = None
    # A comment was posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
    # Create a Comment object without saving it to the database
        comment = form.save(commit=False)
    # Assign the post to the comment
        comment.post = post
    # Save the comment to the database
        comment.save()
    return render(request, 'blog/post/comment.html',
                                                {'post': post,
                                                'form': form,
                                                'comment': comment})



def post_list(request):
    posts = Post.published.all()
    # paginator = Paginator(post_list, 3)
    # page_number = request.GET.get('page', 1)
    # posts = paginator.page(page_number)
    
    return render(request,
                        'blog/post/list.html',
                        {'posts': posts})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                                        status=Post.Status.PUBLISHED,
                                        slug=post,
                                        publish__year=year,
                                        publish__month=month,
                                        publish__day=day)
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    # Form for users to comment
    form = CommentForm()
    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                                        .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                                        .order_by('-same_tags','-publish')[:4]
    return render(request,
                        'blog/post/detail.html',
                        {'post': post,
                         'comments': comments,
                          'form': form,
                          'similar_posts': similar_posts})

def post_search(request):
    form = SearchForm()
    query = None
    results = []
    
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('body', weight='B')
            search_query = SearchQuery(query, config='spanish')
            results = Post.published.annotate(
                            search=search_vector,similarity=TrigramSimilarity('title', query),
                            rank=SearchRank(search_vector, search_query)
                            ).filter(rank__gte=0.3,similarity__gt=0.1).order_by('-rank','-similarity')
    return render(request,
                            'blog/post/search.html',
                            {'form': form,
                            'query': query,
                            'results': results})