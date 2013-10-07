#!/usr/bin/env python

import MySQLdb
import time

class bugsQuery:
    """Class to help with Bugzilla queries.  If the class is not initialized with a product name, then the class will default to 'rds'.  """
    
    status_preferred_order = ['NEW','CODE','TEST','BUILD','SIGNOFF','LOAD','RELEASE']
    
    #local bugzilla database information defaults
    dbhost = "******"
    database = "******"
    dbuser = "******"
    dbpassword = "******"
    product_id = "******"  #for the Product
    
    #Dashboard settings override
    try:
        import dash.settings
        dbhost = dash.settings.BUGZILLA_DB_HOSTNAME
        database = dash.settings.BUGZILLA_DATABASE_NAME
        dbuser = dash.settings.BUGZILLA_DATABASE_USER
        dbpassword = dash.settings.BUGZILLA_DATABASE_PASSWORD
    except:
        print time.ctime(),"INFO No dashboard settings found, working as lib only."
    
    def __init__(self,product='rds',iteration_connector_preference='target_milestone'):
        try:
            self.db = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpassword, db=self.database)
            self.c = self.db.cursor()
        except:
            print time.ctime(),"WARNING Unable to connect to Bugzilla database."

        #the following connects iterations with either target milestones or versions, preference here
        self.connector_preference = iteration_connector_preference   
            
        try:
            self.c.execute("""select products.id from products where products.name= %s""", (product.lower(),))
            self.product = product.lower()
            sql_data = self.c.fetchall()
            self.product_id = sql_data[0][0]
        except:
            print time.ctime(),"ERROR Product name is invalid."

    def packageBugData(self,data):
        print data
        bug_data = []
        for row in data:
            f = {"id":row[0], "status":row[1], "desc":row[2]}
            bug_data.append(f)
        return bug_data
        
    def getUserIdFromName(self,name):
        login_name = name
        self.c.execute("""select profiles.userid from profiles where login_name= %s""", (login_name,))
        userid = self.c.fetchall()
        return userid[0][0]
        
    def getNameFromUserId(self,user_id):
        self.c.execute("""select profiles.login_name from profiles where userid= %s""", (user_id,))
        email_name = self.c.fetchall()
        login_name = email_name[0][0].split('@')
        return login_name[0]

    def getBugsForUser(self,name):
        userid = self.getUserIdFromName(name)
        self.c.execute("""select bugs.bug_id,bugs.bug_status,bugs.short_desc from bugs \
                       where bugs.product_id = %s and bugs.assigned_to = %s""",(self.product_id,userid,))
        bugs = self.c.fetchall()
        return bugs
        
    def getBugsForUserAndIteration(self,name,iteration):
        userid = self.getUserIdFromName(name)
        self.c.execute("""select bugs.bug_id,bugs.bug_status,bugs.short_desc from bugs \
                       where bugs.product_id = %s and bugs.assigned_to = %s and bugs.target_milestone = %s""", \
                       (self.product_id,userid,iteration,))
        raw_data = self.c.fetchall()
        return self.packageBugData(raw_data)

    def getBugNumbersForIteration(self,iteration):
        print self.product_id, self.connector_preference, iteration

        self.c.execute("""select bugs.assigned_to,count(bugs.assigned_to) bug_count \
                       from bugs where bugs.product_id=%s and bugs.target_milestone=%s \
                       and bugs.bug_status not like "CLOSED" group by bugs.assigned_to order \
                       by bug_count DESC""", (self.product_id,iteration,))
        raw_data = self.c.fetchall()

        bug_stats_list =[]
        for item in raw_data:
            name = self.getNameFromUserId(item[0])
            bug_stats_list.append([name,item[1]])
        
        return bug_stats_list
    
    def getTotalBugNumbersByPerson(self):
        self.c.execute("""select bugs.assigned_to,count(bugs.assigned_to) bug_count \
                       from bugs where bugs.product_id=%s \
                       and bugs.bug_status not like "CLOSED" group by bugs.assigned_to order \
                       by bug_count DESC""", (self.product_id,))
        raw_data = self.c.fetchall()

        bug_stats_list =[]
        for item in raw_data:
            name = self.getNameFromUserId(item[0])
            bug_stats_list.append([name,item[1]])
        
        return bug_stats_list
    
    def getTotalBugNumbersByStatus(self):
        self.c.execute("""select bugs.bug_status,count(bugs.bug_status) bug_count \
                       from bugs where bugs.product_id=%s \
                       and bugs.bug_status not like "CLOSED" group by bugs.bug_status""", (self.product_id,))
        raw_data = self.c.fetchall()
  
        bug_status_count = {}
        for return_line in raw_data:
            bug_status_count[return_line[0]] = return_line[1]
            
        bug_status_count_ordered = []
        for status in self.status_preferred_order:
            try:
                bug_status_count_ordered.append({status:bug_status_count[status]})
            except:
                bug_status_count_ordered.append({status:0})

        return bug_status_count_ordered