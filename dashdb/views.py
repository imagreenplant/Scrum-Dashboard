# Create your views here.

import dashdb.models

class ConfigViews:
    def getBacklogsForTeam(self,given_team):
        return dashdb.models.Backlog.objects.filter(team__name=given_team)
        
    def getMainBacklogsForTeam(self,given_team):
        return dashdb.models.Backlog.objects.filter(team__name=given_team).filter(supplemental=False)
        
    def getIterationsForBacklog(self,given_backlog):
        return dashdb.models.Iteration.objects.filter(backlog__backlog=given_backlog)
        
    def getAllTeams(self):
        return dashdb.models.Team.objects.all()
        
