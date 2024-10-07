from django.urls import path

from . import views


app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path(
        'posts/<int:post_id>/edit/', views.PostUpdateView.as_view(),
        name='edit_post'
    ),
    path(
        'posts/<int:post_id>/comment/', views.AddCommentView.as_view(),
        name='add_comment'
    ),
    path(
        'posts/<int:post_id>/edit_comment/<int:pk>/',
        views.EditCommentView.as_view(), name='edit_comment'
    ),
    path(
        'posts/<int:post_id>/delete/', views.PostDeleteConfirmView.as_view(),
        name='delete_post'
    ),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.CommentDeleteConfirmView.as_view(), name='delete_comment'
    ),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
]
