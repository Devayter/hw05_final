from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    list_editable = ('group',)


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'description',)
    search_fields = ('title',)
    list_filter = ('title',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'post',)
    search_fields = ('author', 'post',)
    list_filter = ('author', 'post',)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
    search_fields = ('user', 'author',)
    list_filter = ('user', 'author',)


admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
