#!/usr/bin/env python

import psycopg2
import operator
import time
import datetime

class sninjaQuery:
    """
    Class to help with Scrum Ninja queries.  Whichever project this class in instantiated with will become the standard project for
    all of the below queries/methods.
    """
    
    #Scrum Ninja database information defaults
    dbhost = "******"
    database = "******"
    dbuser = "******"
    dbpassword = "******"
    
    #Dashboard settings override
    try:
        import dash.settings
        dbhost = dash.settings.SCRUMNINJA_DB_HOSTNAME
        database = dash.settings.SCRUMNINJA_DATABASE_NAME
        dbuser = dash.settings.SCRUMNINJA_DATABASE_USER
        dbpassword = dash.settings.SCRUMNINJA_DATABASE_PASSWORD
    except:
        print time.ctime(),"INFO No dashboard settings found, working as lib only."

    iterations_grabbed = False
    projectId = False
    
    def __init__(self,project):
        self.db = psycopg2.connect(host=self.dbhost, user=self.dbuser, password=self.dbpassword, database=self.database)
        self.c = self.db.cursor()
        self.project_name = project
        self.projectId = self.getProjectIdFromProjectName()
        
    def packageTaskData(self,data):
        """ This function helps to package the data for tasks, for use by django and its context object"""
        task_data = []
        for row in data:
            f = {"task":row[0], "story":row[1], "status":row[2]}
            task_data.append(f)
        return task_data
        
    def getUserIdFromName(self,username):
        """looks up user's id from database, based on user's email"""
        sql_string = "'" + username + "%'"
        print sql_string
        self.c.execute("""select users.id from users where users.email like %s""", (username + "%",))
        print username
        userid = self.c.fetchall()
        print userid
        if userid:
            return userid[0][0]
        else:
            return False
        
    def getProjectIdFromProjectName(self):
        """looks up the project id from the inputted project name.  First it looks for an exact match, then a substring match. i.e.
        'recengine' will match for 'RDS->RecEngine' """
        self.c.execute("""select projects.id,projects.name from projects""")
        all_projects = self.c.fetchall()
        for project in all_projects:   #looks for exact match
            if project[1].lower() == self.project_name.lower():
                self.projectId = project[0]
                return project[0]
        for project in all_projects:   #looks for substring match
            if project[1].lower().find(self.project_name.lower()) > -1:  #this finds the url substring, like recengine in RDS->recengine
                self.projectId = project[0]
                return project[0]
                
    def getProjectIdsFromProjectNames(self,project_list):
        """looks up the project ids from the inputted project names.  First it looks for an exact match, then a substring match. i.e.
        'recengine' will match for 'RDS->RecEngine'.  This is a specialized function to grab external project names in addition to the ones
        instantiated in this object."""
        found_project_ids = []
        
        self.c.execute("""select projects.id,projects.name from projects""")
        all_projects = self.c.fetchall()
        for name in project_list:
            exact_match_found = False
            for project in all_projects:   #looks for exact match
                if project[1].lower() == name.lower():
                    found_project_ids.append(str(project[0]))
                    exact_match_found = True
            if exact_match_found == False:
                for project in all_projects: 
                    if project[1].lower().find(name.lower()) > -1: #this finds the url substring, like recengine in RDS->recengine
                        found_project_ids.append(str(project[0]))
                                                 
        return found_project_ids
        
    
    def checkForProjectId(self):
        """ internal function to see if the class's project ID has been set yet """
        if not self.projectId:
            self.getProjectIdFromProjectName()
    
    def getSumOfStoryPointsForProject(self):
        """
        Get the total number of story points, including the history, backlog, and current iteration.  The
        story points come from the project name that the sninjaQuery class was instantiated with.
        """
        project_id = self.getProjectIdFromProjectName()
        
        if project_id:
            self.c.execute("""select stories.name,stories.complexity from stories,story_collections \
                           where ((story_collections.project_id=%s) and (story_collections.id=stories.story_collection_id))""",(project_id,))
            story_point_raw_data = self.c.fetchall()
            
            STORY_POINT_SUM = 0
            check = 0
            for row in story_point_raw_data:
                try:
                    check = int(row[1])
                except:
                    check = False
                    
                if check:
                    STORY_POINT_SUM += check
                    
            return STORY_POINT_SUM
        
        else:
            return False
        
    def getIterationsAndIdsForProject(self):
        """Given a project id, this will grab all of the iterations(story_collections) and their ids for the project."""
        self.iteration_dict = {}
        project_id = self.getProjectIdFromProjectName()
        if project_id:
            self.c.execute("""select story_collections.goal,story_collections.id \
                           from story_collections where story_collections.project_id=%s;""",(project_id,))
            iterations_raw_data = self.c.fetchall()
            
            if iterations_raw_data:
                self.iterations_grabbed = True
                for row in iterations_raw_data:
                    if row[0]:
                        self.iteration_dict[row[0].lower()] = row[1]
                    else:
                        self.iteration_dict['backlog'] = row[1]
                return self.iteration_dict
        else:
            return False
           
    def getIterationIdFromName(self,iteration):
        """Gets an iteration id from inputted name.  This also checks to make sure that name is in the available iterations in the database."""
        if not self.iterations_grabbed:
            self.getIterationsAndIdsForProject()
            
        iter_lower_case = iteration.lower()
        if iter_lower_case in self.iteration_dict.keys():  #checks to make sure this exists in the database's iterations for a project
            return self.iteration_dict[iter_lower_case]
        else:
            return False
        
    def getIterationNameFromId(self,iteration_id):
        """Gets an iteration name from inputted id."""
        if iteration_id:
            self.c.execute("""select story_collections.goal from story_collections \
                           where story_collections.id=%s;""",(iteration_id,))
            return self.c.fetchall()[0][0]
        else:
            return False
        
    def getTasksForUserAndIteration(self,username,iteration):
        """Grabs all the tasks for a user in an iteration."""
        userid = self.getUserIdFromName(username)
        iteration_id = self.getIterationIdFromName(iteration)
        
        print userid, iteration_id
        
        if iteration_id and userid:
            self.c.execute("""select tasks.name,stories.name,tasks.status from tasks,stories,story_collections \
                           where ((stories.id=tasks.story_id) AND (story_collections.id=stories.story_collection_id) \
                           AND (story_collections.id=%s) AND (tasks.assigned_to_user_id=%s))""",(iteration_id,userid,))
            tasks_raw_data = self.c.fetchall()
            return self.packageTaskData(tasks_raw_data)
        else:
            return False
        
    def getUnclaimedTasksForIteration(self,iteration):
        """Gets all the Unclaimed Tasks for an iteration."""
        iteration_id = self.getIterationIdFromName(iteration)
        
        if iteration_id:
            self.c.execute(""" select tasks.name,stories.name from tasks,stories,story_collections \
                           where ((stories.id=tasks.story_id) AND (story_collections.id=stories.story_collection_id) \
                           AND (story_collections.id=%s) AND (tasks.assigned_to_user_id IS NULL))""",(iteration_id,))
            tasks_raw_data = self.c.fetchall()
            
            task_data = []
            for row in tasks_raw_data:
                g = {"task":row[0], "story":row[1]}
                task_data.append(g)
            return task_data
        else:
            return False
        
    def getStoryCollections(self):
        """Gets all the iterations (story_collections) for a project."""
        self.checkForProjectId()
        
        self.c.execute("""select story_collections.id,story_collections.number,story_collections.type,story_collections.goal from story_collections \
                       where story_collections.project_id=%s """,(self.projectId,))
        
        collections_raw_data = self.c.fetchall()
        
        collections_raw_data.sort(key=operator.itemgetter(1))
        return collections_raw_data
    
    def getStoryCollectionsWithoutBacklog(self):
        return self.getStoryCollections()[1:]
        
    
    def getIterations(self):
        iteration_data = self.getStoryCollections()
        iterations = []
        
        for entry in iteration_data[1:]:  #removes the backlog, which is the first id
            iterations.append(entry[3])
            
        return iterations
    
    def getCurrentIterationId(self):
        iteration_data = self.getStoryCollections()
        current_iteration_id = iteration_data[-1]
        
        return current_iteration_id[0]
        
    def getStoriesForCurrentIteration(self):
        current_id = self.getCurrentIterationId()
        current_stories = []
        
        self.c.execute("""select stories.name,stories.complexity,stories.position,stories.status from stories \
                           where stories.story_collection_id=%s """,(current_id,))
        current_stories_raw_data = self.c.fetchall()
        for story in current_stories_raw_data:
            current_stories.append(story)
        current_stories.sort(key=operator.itemgetter(2))
        
        return current_stories
        
    def getIterationsReversed(self):
        iterations = self.getIterations()
        iterations.reverse()
        return iterations
        
    def getHistoricalStoryCollectionIds(self):
        historical_id_list = []
        data = self.getStoryCollections()
        
        if len(data) > 2: #checks if there are historical sprints
            data.remove(data[0])  #removes the backlog
            data.remove(data[-1])  #removes the current sprint
            return data
        else:
            return False
    
    def getStoryCollectionIdsForSupplementalProject(self):
        """
        This returns the collection of iteration ids you will want for a planning exercise, IF the project is
        a supplemental project.  A supplemental project is one that doesn't have work being done on it, but
        is used to track stories in a particular bucket.  For instance, RDS->Swordfish or RDS->Internal.
        """
        
        id_list = []
        data = self.getStoryCollections()
        edited_list = [data[0],data[-1]]
        for item in edited_list:
            id_list.append(item[0])
        return id_list
    
    def getBacklogIdForMainProject(self):
        """
        Every project has one, and only one, backlog ID in scrum ninja.
        This grabs that ID for use in getting backlog information.
        """  
        data = self.getStoryCollections()
        list = [data[0][0]]
        return list   #returns backlog id   
        
    def getTopStories(self,supplemental_flag=False):
        """
        Gets all the topmost non-deployed stories for a project.  If the
        supplemental flag is on, then it will pull the stories that include the
        ones in the current active sprint.  (This is needed for the RDS child
        backlogs).  The default behavior is to take only those from the next
        sprint and beyond (needed for RDS mother backlog).
        """
        topStories = []
        if supplemental_flag:
            data = self.getStoryCollectionIdsForSupplementalProject()
        else:
            data = self.getBacklogIdForMainProject()
        
        for id in sorted(data, reverse=True):
            self.c.execute("""select stories.name,stories.complexity,stories.position from stories \
                           where stories.story_collection_id=%s and (status is null or status='rejected')""",(id,))
            stories_raw_data = self.c.fetchall()
            for story in stories_raw_data:
                topStories.append(story)
                
        topStories.sort(key=operator.itemgetter(2))
        return topStories
    
    def getTopOncallStories(self):
        topStories = []
        iteration_id_list = [self.getCurrentIterationId(),self.getBacklogIdForMainProject()[0]]
        
        for id in iteration_id_list:
            print "id is", id
            self.c.execute("""select stories.name,stories.complexity,stories.position,stories.status from stories \
                               where stories.story_collection_id=%s """,(id,))
            stories_raw_data = self.c.fetchall()
            for story in stories_raw_data:
                    topStories.append(story)            
        topStories.sort(key=operator.itemgetter(2))
        return topStories

    def getTotalVelocityForIterationId(self,iteration_id):
        point_sum = 0
        self.c.execute("""select stories.complexity from stories \
                        where stories.story_collection_id=%s""",(iteration_id,))
        historical_story_points = self.c.fetchall()
        
        for story_point in historical_story_points:
            try:
                check = int(story_point[0])
            except:
                check = False
                    
            if check:
                point_sum += check
                
        return point_sum
    
    def getDateEndedForIteration(self,iteration_id):
        self.c.execute("""select ends_on from story_collections \
                        where id=%s""",(iteration_id,))
        date_ended = self.c.fetchall()
        date = {}
        
        #Parse out leading 0s, convert to number, and into month/day etc.
        if date_ended:
            date = date_ended[0][0]
            return date
        else:
            return False
    
    def getHistoricalVelocities(self):
        stories_list = []
        ids = self.getHistoricalStoryCollectionIds()
        
        if ids:
            for id in ids:
                point_sum = self.getTotalVelocityForIterationId(id[0])
                date_ended = self.getDateEndedForIteration(id[0])
                stories_list.append([id,point_sum,self.getIterationNameFromId(id[0]),date_ended,id[1]])
                
            stories_list.sort(key=operator.itemgetter(0))  #sort on iteration history
            return stories_list
        else:
            return False
    
    def getAverageHistoricalVelocity(self , running_average_cutoff = 3):
        average_velocities = {}
        
        sum = 0
        historical_velocities = self.getHistoricalVelocities()
        
        if historical_velocities:
            for velocity_item in historical_velocities:
                sum += velocity_item[1]
            number_of_iterations = len(historical_velocities)
            average_velocities['total_average']=sum/number_of_iterations
            
            if number_of_iterations > running_average_cutoff:
                recent_sum = 0
                for recent_velocity in historical_velocities[-running_average_cutoff:]:
                    recent_sum += recent_velocity[1]
                average_velocities['running_average'] = recent_sum/running_average_cutoff
            else:
                average_velocities['running_average'] = False
                
            return average_velocities
        else:
            return False
        
    def getTagIdFromTagName(self , tag_name):
        """looks up tag's id from database, based on tag name"""
        self.c.execute("""select tags.id from tags where tags.name= %s""", (tag_name,))
        tag_id = self.c.fetchall()
        if tag_id:
            return tag_id[0][0]
        else:
            return False
        
    def getAllStoriesForTagName(self, tag_name):
        """grabs all the stories with a particular tag, separated by iteration"""
        
        project_id = self.getProjectIdFromProjectName()
        self.c.execute("""select story_collections.goal,stories.name,stories.complexity, \
                       story_collections.ends_on,story_collections.id from stories,tags,taggings,story_collections \
                       where tags.name=%s AND tags.id = taggings.tag_id AND \
                       taggings.taggable_id = stories.id AND stories.story_collection_id = \
                       story_collections.id AND story_collections.project_id = %s \
                       ORDER BY story_collections.ends_on DESC;""", (tag_name,project_id,))
        raw_data = self.c.fetchall()
        
        iteration_dict = {}
        iteration_names = []
        
        for story_data_row in raw_data:
            if story_data_row[0]:
                if story_data_row[0] in iteration_dict.keys():
                    #iteration_data[-1].append([story_data_row[1],story_data_row[2],story_data_row[3]])
                    #iteration_names[story_data_row[0]].append([story_data_row[1],story_data_row[2],story_data_row[3]])
                    iteration_dict[story_data_row[0]]['stories'].append([story_data_row[1],story_data_row[2],story_data_row[3],story_data_row[4]])
                else:
                    #iteration_names[story_data_row[0]] = [[story_data_row[1],story_data_row[2],story_data_row[3]]]
                    #iteration_names.append(story_data_row[0])
                    #iteration_data.append([story_data_row[0]])
                    #iteration_data[-1].append([story_data_row[1],story_data_row[2],story_data_row[3]])
                    iteration_dict[story_data_row[0]] = {}
                    iteration_dict[story_data_row[0]]['stories'] = [[story_data_row[1],story_data_row[2],story_data_row[3],story_data_row[4]]]
                    
        return iteration_dict
    
    def getPointsPerIterationForTag(self, tag_name):
        """Returns dictionary of iterations with total point values for tags."""
        
        iteration_story_dictionary = self.getAllStoriesForTagName(tag_name)
        for iteration in iteration_story_dictionary.keys():
            iteration_story_dictionary[iteration]['total_velocity'] = self.getTotalVelocityForIterationId(self.getIterationIdFromName(iteration))
            tag_velocity_sum = 0
            for story in iteration_story_dictionary[iteration]['stories']:
                try:
                    check = int(story[1])
                except:
                    check = False
                    
                if check:
                    tag_velocity_sum += check
            iteration_story_dictionary[iteration]['tag_velocity'] = tag_velocity_sum
        
        return iteration_story_dictionary
    
    def queryCompletionTimes(self):
        """Returns an array of dates by which to calculate the delta of completion date vs created date."""
        project_id = self.getProjectIdFromProjectName()
        
        self.c.execute("""SELECT 
                              stories.delivered_on, 
                              stories.created_at
                          FROM 
                              public.stories, 
                              public.story_collections, 
                              public.projects
                          WHERE 
                              stories.story_collection_id = story_collections.id AND
                              story_collections.project_id = projects.id AND
                              projects.id = %s AND 
                              stories.created_at IS NOT NULL  AND 
                              stories.delivered_on IS NOT NULL ;""", (project_id,))
        return self.c.fetchall()
        
        
    def getAverageCompletionTime(self):
        """Returns an array of dates by which to calculate the average number of days it takes an item to be delivered."""
        delta_times = self.queryCompletionTimes()
        
        intervals = []
        for delta in delta_times:
            interval = delta[0] - delta[1].date()
            intervals.append(interval.days)
            
        return sum(intervals)/len(intervals)
        
    def getMovingAverageForDays(self,step=3,time_span=7, start_date=datetime.date(2010, 10, 1)):
        """Returns a moving average, given by the step value, for a given time interval. Defaults to 3 day step, 7 day
            interval. Default start day is 10/1/2010."""
            
        # dict of (end date, average)
        moving_average_points = {}
        tdelta = datetime.timedelta(days=step)
        
        focus_date = datetime.date.today() #today
        #find dates to measure
        while focus_date > start_date:
            moving_average_points[focus_date] = 0
            focus_date = focus_date - tdelta
            
        delta_times = self.queryCompletionTimes()  #grab data
        
        for target_date in moving_average_points.keys():
            print "--------- target date ", target_date, "--------------"
            intervals = []
            for date in delta_times:
                if date[0] <= target_date and date[0] >= target_date - datetime.timedelta(days=time_span):
                    print "target date is", target_date, " and date[0] is ", date[0]
                    interval = date[0] - date[1].date()
                    intervals.append(interval.days)
                    
            if len(intervals) > 0:
                moving_average_points[target_date] = sum(intervals)/len(intervals)
                
        return moving_average_points

    def getGlobalStoriesStatusByTag(self, tag_name):
        """Returns list of stories with tasks and comments to relay status of all tagged with x."""
        
        self.c.execute("""SELECT projects.id, projects."name", story_collections."number", story_collections.goal, \
                            story_collections.starts_on, story_collections.ends_on, stories.id, stories."name", stories."content", \
                            stories.complexity, stories.created_at, stories.status, 
                            stories.delivered_on, tags."name", tasks.id, tasks."name", tasks.status, tasks.started_at, \
                            tasks.blocked, users.email \
                        FROM public.story_collections, public.stories, public.tags, public.taggings, public.tasks, \
                            public.projects, public.users \
                        WHERE story_collections.project_id = projects.id AND stories.story_collection_id = story_collections.id AND \
                            stories.id = tasks.story_id AND taggings.tag_id = tags.id AND taggings.taggable_id = stories.id AND \
                            tasks.assigned_to_user_id = users.id AND tags."name" = %s AND story_collections.ends_on >= '11-1-2010' \
                        ORDER BY projects."name" ASC, story_collections.goal ASC;""",(tag_name,))
        
        story_data = self.c.fetchall()
        tagged_stories = {}
        
        for story in story_data:
            if story[0] not in tagged_stories.keys():
                tagged_stories[story[0]] = story[1]

        return story_data,tagged_stories
    
    def getRecentPopularTagsForProjects(self, project_list, days_into_past=90):
        project_ids = self.getProjectIdsFromProjectNames(project_list)
            
        self.c.execute("""SELECT tags."name", count(tags."name") tag_count \
                        FROM public.taggings, public.tags, public.stories, public.story_collections, public.projects \
                        WHERE taggings.taggable_id = stories.id AND taggings.tag_id = tags.id AND \
                            stories.story_collection_id = story_collections.id AND story_collections.project_id = projects.id AND \
                            projects.id in (%s) AND stories.updated_at > DATE 'NOW' - %s
                        GROUP BY tags."name" order by tag_count desc;""" % (",".join(project_ids),days_into_past))
        raw_data = self.c.fetchall()
        
        return raw_data;