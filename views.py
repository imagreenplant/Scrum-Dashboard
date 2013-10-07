from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from djangomako.shortcuts import render_to_response, render_to_string
from django.conf import settings

from dash.dashdb.models import User,Alias,Iteration,Backlog,Tag,Team
from dash.dashdb.views import ConfigViews

import bugsQuery
import sninjaQuery

def root(request):
    template = 'root.html'
    choices = {}

    teams = {}
    teams['data'] = ConfigViews().getAllTeams()
    teams['description'] = 'team'
    teams['url_base'] = '/'  #settings.SITE_PREFIX + '/'
    choices['teams'] = teams

    context_data = {'choices':choices, 'media_url':settings.MEDIA_URL}
    return render_to_response(template, context_data)

def team_root(request, given_team):
    print "Request-----------------------------"
    print request
    print "End request---------------------------"
    template = 'team_root.html'
    data = {}
    data['choices'] = {}
    data['links'] = {}
    
    team_name = given_team.lower()
    
    #team validation
    teams = ConfigViews().getAllTeams()
    if team_name not in teams:
        print "project name not recognized"
        
    #team links
    data['links']['Backlog Summary'] = settings.SITE_PREFIX + '/team/' + team_name + '/backlogs'
    data['links']['Planning'] = settings.SITE_PREFIX + '/team/' + team_name +'/planning'
    data['team_name'] = team_name
    #links['Tag Summary'] = settings.SITE_PREFIX + '/' + team_name.lower() +'/tags'
    
    data['links']['Site Admin'] = settings.SITE_PREFIX + '/admin'
    
    team_settings = Team.objects.get(name=team_name)
    team_backlogs = ConfigViews().getMainBacklogsForTeam(team_name)
        
    if team_settings.show_iterations:
        for backlog in team_backlogs.filter(is_oncall_backlog=False):
            iterations = {}
            #iterations['data'] = Iteration.objects.filter(backlog__team__name=team_name.lower()).filter(display=True)
            iterations['data'] = sninjaQuery.sninjaQuery(backlog.backlog).getIterationsReversed()[:10]
            iterations['description'] = 'iterations of ' + backlog.backlog
            iterations['url'] = settings.SITE_PREFIX + '/product/' + backlog.backlog + '/'
            data['choices']['iterations' + backlog.backlog] = iterations
        
    if team_settings.show_tags:
        tags = {}
        tags['data'] = sninjaQuery.sninjaQuery(backlog.backlog).getRecentPopularTagsForProjects([blg.backlog for blg in team_backlogs])[:15] #Tag.objects.all()
        tags['description'] = 'tag shortcuts'
        tags['url'] = settings.SITE_PREFIX + '/product/' + team_name + '/tag/'
        data['popular_tags'] = tags
        
    if team_settings.show_rds_style_bug_count:
        bugzilla_rds = bugsQuery.bugsQuery(team_name)
        
        bugs_status_count = {}
        bugs_status_count['data'] = bugzilla_rds.getTotalBugNumbersByStatus()
        bugs_status_count['description'] =  'bug count'
        bugs_status_count['url'] = settings.SITE_PREFIX + '/product/' + team_name + '/bugs/'
        data['bugs_status'] = bugs_status_count
        
    if team_settings.show_current_backlogs:
        current_backlogs = []
        
        for backlog in team_backlogs.filter(is_oncall_backlog=False):
            backlog_info = {}
            backlog_info['stories'] = sninjaQuery.sninjaQuery(backlog.backlog).getStoriesForCurrentIteration()
            backlog_info['description'] = backlog.backlog
            backlog_info['url'] = settings.SITE_PREFIX + '/backlog/' + backlog.backlog + '/'
            current_backlogs.append(backlog_info)
        data['current_backlogs'] = current_backlogs
        
    if team_settings.show_oncall_backlog:
        oncall_backlogs = []

        for oncall_type in team_backlogs.filter(is_oncall_backlog=True):
            oncall_info = {}
            oncall_info['stories'] = sninjaQuery.sninjaQuery(oncall_type.backlog).getTopOncallStories()
            oncall_info['description'] = oncall_type.backlog
            oncall_info['url'] = settings.SITE_PREFIX + '/backlog/' + oncall_type.backlog + '/'
            oncall_backlogs.append(oncall_info)

        data['oncall_backlogs'] = oncall_backlogs
        
    context_data = {'data':data, 'media_url':settings.MEDIA_URL}
    return render_to_response(template, context_data)

def status(request):
    dumbData = "A ok, captain!"
    return HttpResponse(dumbData)

def iteration(request,project_name,iteration_name):
    """
    This view returns the iteration specific page, i.e. the Spoon iteration
    of RDS.
    """
    iterations = sninjaQuery.sninjaQuery(project_name).getStoryCollections
    name_test = Iteration.objects.filter(iteration=iteration_name)
    
    if name_test:
        #getting bug stats
        
        bugClass = bugsQuery.bugsQuery(project_name)
        bug_stats = bugClass.getBugNumbersForIteration(iteration_name)
        
        #getting task data
        taskClass = sninjaQuery.sninjaQuery(project_name)
        task_stats = taskClass.getUnclaimedTasksForIteration(iteration_name)
        
        template = 'iteration_dash.html'
        context_data = {'bugStats': bug_stats, 'iteration':iteration_name, 'taskStats':task_stats, 'media_url':settings.MEDIA_URL}
        return render_to_response(template, context_data)
    else:
        template= 'try_again-iteration.html'
        context_description = 'iteration'
        all_choices = []
        iterations = Iteration.objects.all()
        for entry in iterations:
            all_choices.append(entry.iteration)
        context_data = {'bad_content':iteration_name, 'all_choices':all_choices, 'type':context_description, 'media_url':settings.MEDIA_URL}
        return render_to_response(template, context_data)

def member_iteration(request,project_name,iteration,name):
    """
    This view returns the member-specific per iteration view, i.e mlapora's
    status for the Spoon iteration.
    """
    user_test = User.objects.filter(username=name)
    alias_test = Alias.objects.filter(alias=name)

    if user_test or alias_test:
        template = 'member_iter.html'
        
        #getting bug data
        b = bugsQuery.bugsQuery(project_name)
        c = b.getBugsForUserAndIteration(name,iteration)
        #getting task data
        d = sninjaQuery.sninjaQuery(project_name)

        if user_test:
            e = d.getTasksForUserAndIteration(user_test[0].email,iteration)
        else:
            e = d.getTasksForUserAndIteration(alias_test[0].email,iteration)
        
        context_data = {'member_name': name,'iteration':iteration, 'bugs': c, 'tasks':e, 'media_url':settings.MEDIA_URL}
        return render_to_response(template, context_data)
        
    else:   #modify the below to use users
        template= 'try_again-iteration.html'
        context_description = 'username'
        users = User.objects.all()
        all_choices = []
        for entry in users:
            all_choices.append(entry.username)
        context_data = {'bad_content':name, 'all_choices':all_choices, 'type':context_description, 'media_url':settings.MEDIA_URL}
        return render_to_response(template, context_data)    
        
def backlogs(request, team_name):
    """
    This view returns the summary of all backlogs under the team umbrella.
    """
    template = 'backlogs.html'
    team = Team.objects.get(name=team_name.lower())
    backlogs = Backlog.objects.filter(team=team.id)
    
    #--------------------------------------------------------------
    items_to_display = team.backlog_items_shown #default # of items to display per backlog
    #--------------------------------------------------------------
    
    mother_backlog_stats = {}
    supplemental_backlog_stats = {}
    
    for backlog in backlogs:
        a = sninjaQuery.sninjaQuery(backlog.backlog)
        project_id = a.getProjectIdFromProjectName()
        if project_id:
            if not backlog.supplemental:
                mother_backlog_stats[backlog.backlog] = {}
                mother_backlog_stats[backlog.backlog]['data'] = a.getTopStories(backlog.supplemental)
                mother_backlog_stats[backlog.backlog]['owner'] = backlog.owner
                mother_backlog_stats[backlog.backlog]['project_id'] = project_id
            if backlog.supplemental:
                supplemental_backlog_stats[backlog.backlog] = {}
                supplemental_backlog_stats[backlog.backlog]['data'] = a.getTopStories(backlog.supplemental)
                supplemental_backlog_stats[backlog.backlog]['owner'] = backlog.owner
                supplemental_backlog_stats[backlog.backlog]['project_id'] = project_id

    # These 3 arrays comprise the three columns that will be created on the html
    # page.  This is a preprocessor for the data.3
    backlog_box1 = {}
    backlog_box2 = {}
    backlog_box3 = {}
    n = 0
    for item in supplemental_backlog_stats.keys():
        print item, n
        if n % 3 == 0:
            backlog_box1[item] = supplemental_backlog_stats[item]
        elif n % 3 == 1:
            backlog_box2[item] = supplemental_backlog_stats[item]
        elif n % 3 == 2:
            backlog_box3[item] = supplemental_backlog_stats[item]
        n += 1
    n = 0
    for item in mother_backlog_stats.keys():
        print item, n
        if n % 3 == 0:
            backlog_box1[item] = mother_backlog_stats[item]
        elif n % 3 == 1:
            backlog_box2[item] = mother_backlog_stats[item]
        elif n % 3 == 2:
            backlog_box3[item] = mother_backlog_stats[item]
        n += 1

    context_data = {'backlog_box1': backlog_box1, 'backlog_box2': backlog_box2, \
                    'backlog_box3': backlog_box3, 'items_to_display': items_to_display, \
                    'media_url':settings.MEDIA_URL}
    return render_to_response(template, context_data)

def backlog(request, backlog_name):
    """
    This view returns the summary of one backlogs and 3 extra sprints.
    """
    template = 'backlog.html'
    
    mother_backlog_stats = {}
    supplemental_backlog_stats = {}
    
    backlog_object = sninjaQuery.sninjaQuery(backlog_name)
    project_id = backlog_object.getProjectIdFromProjectName()
    if project_id:
        backlog_stats = {}
        backlog_stats['data'] = backlog_object.getTopStories(True)
        backlog_stats['project_id'] = project_id
        backlog_stats['name'] = backlog_name

    context_data = {'backlog_box': backlog_stats,'media_url':settings.MEDIA_URL}
    return render_to_response(template, context_data)
    
def planning(request, team_name):
    template = 'planning.html'
    velocities = {}
    datapoints = 0
    column_id = 1
    
    team_backlogs = ConfigViews().getMainBacklogsForTeam(team_name)
    
    for backlog in team_backlogs:
        project_object = sninjaQuery.sninjaQuery(backlog.backlog)
    
        historical_velocities = project_object.getHistoricalVelocities()
        avg_velocities = project_object.getAverageHistoricalVelocity()
        
        if historical_velocities:
            velocities[backlog.backlog] = {'avg_velocity':avg_velocities,'velocities':historical_velocities,'column_id':column_id}
            column_id += 3
            datapoints += len(historical_velocities)

    context_data = {'velocities': velocities,'team_name':team_name, 'datapoints':datapoints, 'media_url':settings.MEDIA_URL}
    return render_to_response(template, context_data)
    
def tags(request):   #summary page
    template = 'tag_summary.html'
    
    project_object = sninjaQuery.sninjaQuery(project_name)

    velocities = project_object.getHistoricalVelocities()
    avg_velocities = project_object.getAverageHistoricalVelocity()
    
    context_data = {'avg_velocities': avg_velocities,'project_name':project_name, 'velocities': velocities, 'media_url':settings.MEDIA_URL}
    return render_to_response(template, context_data)
    
def tag(request, project_name, tag_name):
    template = 'tag.html'
        
    tag_object = sninjaQuery.sninjaQuery(project_name)
    tag_history = tag_object.getPointsPerIterationForTag(tag_name)
    iteration_history = tag_object.getIterationsReversed()
    
    context_data = {'iteration_history':iteration_history,'tag_history': tag_history,'project_name':project_name, 'tag_name':tag_name, 'media_url':settings.MEDIA_URL}
    return render_to_response(template, context_data)