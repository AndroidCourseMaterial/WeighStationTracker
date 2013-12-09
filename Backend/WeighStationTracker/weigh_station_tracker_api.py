'''
Created on Dec 2, 2013

@author: boutell
'''

from google.appengine.ext import ndb
from models import WeighStation, WeighStationStatus
import endpoints
from protorpc import remote
from google.appengine.ext import db

USING_OAUTH = True
DEFAULT_EMAIL = 'default@gmail.com'

@endpoints.api(name='weighstationtracker', version='v1', description='Weigh Station Tracker API', 
               hostname = 'weigh-station-tracker.appspot.com')
class WeighStationTrackerApi(remote.Service):

    @WeighStation.method(name='weighstation.insert', path = 'weighstation/insert', http_method='POST', user_required=False)
    def weigh_station_insert(self, weigh_station):
        ''' Add a new weigh station or edit an existing one'''
        weigh_station.put()
        return weigh_station

    @WeighStationStatus.method(name='weighstationstatus.insert', path = 'weighstationstatus/insert', http_method='POST', user_required=USING_OAUTH)
    def weigh_station_status_insert(self, weigh_station_status):
        ''' Add or edit a status for weigh station. '''
        if USING_OAUTH:
            weigh_station_status.email = endpoints.get_current_user().email().lower()
        else:
            weigh_station_status.email = DEFAULT_EMAIL 
            
        weigh_station_key = ndb.Key(WeighStation, weigh_station_status.weigh_station_id)
        weigh_station_for_status = weigh_station_key.get()
        if weigh_station_for_status is None:
            raise endpoints.NotFoundException('Weigh station id not found')
        weigh_station_status.parent= weigh_station_for_status # Keep both in the same entity group so that transactions could be used.
        weigh_station_status.put()
        return weigh_station_status

    @WeighStation.query_method(query_fields = ('state', 'limit', 'order', 'pageToken'), name='weighstation.list', path = 'weighstation/list', http_method='GET', user_required = False)
    def weigh_station_list(self, query):
        ''' List all weigh stations '''
        return query
    
    @WeighStationStatus.query_method(query_fields = ('weigh_station_id', 'limit', 'order', 'pageToken'), name='weighstationstatus.list', path = 'weighstationstatus/list/{weigh_station_id}', http_method='GET', user_required = False)
    def weigh_station_status_list(self, query):
        ''' List all statuses for the given weigh station '''
        return query

    @db.transactional
    @WeighStation.method(request_fields = ('id',), name='weighstation.delete', path = 'weighstation/delete/{id}', http_method='DELETE', user_required = USING_OAUTH)
    def weigh_station_delete(self, weigh_station):
        ''' Delete the given weigh station and all associated statuses if you are an admin '''      
        if USING_OAUTH:
            if endpoints.get_current_user().email().lower() != 'boutell@gmail.com':
                raise endpoints.ForbiddenException('Only admins are allowed to delete weigh stations')
            
        if not weigh_station.from_datastore:
            raise endpoints.NotFoundException('No weigh station found for the given ID')
 
        query = WeighStationStatus.query().filter(WeighStationStatus.weigh_station_id == weigh_station.key.id())
        for status in query:
            status.key.delete()
        
        weigh_station.key.delete()
        return WeighStation(name='deleted')
    
    @WeighStationStatus.method(request_fields = ('id',), name='weighstationstatus.delete', path = 'weighstationstatus/delete/{id}', http_method='DELETE', user_required = USING_OAUTH)
    def weigh_station_status_delete(self, weigh_station_status):
        ''' Delete the given status assuming you were the creator '''
        if not weigh_station_status.from_datastore:
            raise endpoints.NotFoundException('No weigh station found for the given ID')
        
        if USING_OAUTH:
            if endpoints.get_current_user().email().lower() != weigh_station_status.email:
                raise endpoints.ForbiddenException('Can only delete a status you entered')
        
        weigh_station_status.key.delete()
        return WeighStationStatus(status='deleted')


app =  endpoints.api_server([WeighStationTrackerApi], restricted=False)   