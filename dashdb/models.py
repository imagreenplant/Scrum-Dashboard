from django.db import models

class Changeset(models.Model):
    changeset = models.CharField(max_length=50)
    date = models.DateTimeField(null=True)
    desc = models.CharField(max_length=200, blank=True)
    branch = models.ForeignKey('Branch')
    user = models.ForeignKey('User')
    class Meta:
        verbose_name_plural = 'changesets'
    
    def __unicode__(self):
        return self.desc

class Branch(models.Model):
    branchname = models.CharField(max_length=30)
    class Meta:
        verbose_name_plural = 'branches'
        
    def __unicode__(self):
        return self.branchname

class User(models.Model):
    username = models.CharField(max_length=30)
    fullname = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    teams = models.ManyToManyField('Team')
    class Meta:
        verbose_name_plural = 'users'
        ordering = ('username',)
    def __unicode__(self):
        return self.username

class Alias(models.Model):
    alias = models.CharField(max_length=100)
    user = models.ForeignKey('User')
    class Meta:
        verbose_name_plural = 'aliases'
        ordering = ('user',)
    def __unicode__(self):
        return self.alias
    
class Iteration(models.Model):
    iteration = models.CharField(max_length=20)
    backlog = models.ForeignKey('Backlog', default='')
    display = models.BooleanField(default=True)
    class Meta:
        verbose_name_plural = 'iterations'
        ordering = ('iteration',)

    def __unicode__(self):
        return self.iteration
    
class Backlog(models.Model): #aka project
    backlog = models.CharField(max_length=30)
    supplemental = models.BooleanField(default=False)
    owner = models.CharField(max_length=30, default='')
    team = models.ForeignKey('Team', default='')
    is_oncall_backlog = models.BooleanField(default=False) #oncall type of backlog, like RDS->Lamb
    
    class Meta:
        verbose_name_plural = 'backlogs'
        ordering = ('backlog',)

    def __unicode__(self):
        return self.backlog
    
class Tag(models.Model):
    name = models.CharField(max_length=30)
    backlog = models.ForeignKey('Backlog', default='RDS')
    team = models.ForeignKey('Team', default='')
    class Meta:
        verbose_name_plural = 'tags'
        ordering = ('name',)
    def __unicode__(self):
        return self.name
    
class Team(models.Model):
    name = models.CharField(max_length=30)
    backlog_items_shown = models.PositiveSmallIntegerField(default='6')
    show_iterations = models.BooleanField(default=False)
    show_tags = models.BooleanField(default=False)
    show_rds_style_bug_count = models.BooleanField(default=False)
    show_current_backlogs = models.BooleanField(default=False)
    show_oncall_backlog = models.BooleanField(default=False)
    class Meta:
        verbose_name_plural = 'teams'
        ordering = ('name',)
    def __unicode__(self):
        return self.name