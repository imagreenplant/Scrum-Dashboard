from django.contrib import admin
from dash.dashdb.models import Changeset,Branch,User,Alias,Iteration,Backlog,Tag,Team

class ChangsetAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'desc','date',)
    list_filter = ('user','date',)
    date_hierarchy = 'date'
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branchname',)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'fullname', 'email',)
    search_fields = ('username',)
class AliasAdmin(admin.ModelAdmin):
    list_display = ('alias','user',)
class IterationAdmin(admin.ModelAdmin):
    list_display = ('iteration','backlog','display')
    list_filter = ('backlog',)
class BacklogAdmin(admin.ModelAdmin):
    list_display = ('backlog','supplemental','owner','team','is_oncall_backlog',) 
    list_filter = ('team',)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name','team','backlog',)
    list_filter = ('team',)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name','backlog_items_shown','show_iterations','show_tags','show_rds_style_bug_count', \
                    'show_current_backlogs','show_oncall_backlog',)

admin.site.register(Changeset, ChangsetAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Alias, AliasAdmin)
admin.site.register(Iteration, IterationAdmin)
admin.site.register(Backlog, BacklogAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Team, TeamAdmin)
