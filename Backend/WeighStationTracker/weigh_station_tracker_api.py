'''
Created on Dec 2, 2013

@author: boutell
'''

from google.appengine.api.search.search import GeoPoint
from google.appengine.ext import db, ndb
from models import WeighStation, WeighStationStatus, WeighStationLocationMessage
from protorpc import remote
import endpoints
import logging
import math

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

    @WeighStation.query_method(query_fields = ('limit', 'order', 'pageToken'), name='weighstation.list', path = 'weighstation/list', http_method='GET', user_required = False)
    def weigh_station_list(self, query):
        ''' List all weigh stations '''
        return query
    
    @WeighStation.query_method(query_fields = ('state', 'limit', 'order', 'pageToken'), name='weighstation.listbystate', path = 'weighstation/listbystate/{state}', http_method='GET', user_required = False)
    def weigh_station_list_by_state(self, query):
        ''' List all weigh stations '''
        return query
    
# Close to working, but can't figure out how to get geopoint out of the query parameter!
#    @WeighStation.query_method(query_fields = ('latitude', 'longitude', 'limit', 'order', 'pageToken'), name='weighstation.listbylocation', path = 'weighstation/listbylocation', http_method='GET', user_required = False)
#    def weigh_station_list_by_location(self, query):
#        ''' List all weigh stations '''
#        # Much too brittle!
#        lat_string = str(query.filters)
#        lat_tokens = lat_string.split(',')
#        logging.info('lat query = ' + str(lat_tokens))
#        lat = lat_tokens[-1].split(')')[0]
#        logging.info('lat query = '+ lat)
#        lat = float(lat.strip())
#        logging.info(str(lat))
#        query = WeighStation.query()
#        for weigh_station in query:
#            logging.info(weigh_station)
#            longitude = weigh_station.longitude
#        return query
    
    # A workaround for the failed attempt above.
    @WeighStationLocationMessage.method(name='wslm', path = 'wslm', http_method='POST', user_required = False)
    def weigh_station_location_message(self, wslm):
        user_location = GeoPoint(wslm.latitude, wslm.longitude)
        query = WeighStation.query()
        sorted_weigh_stations = []
        for weigh_station in query:
            logging.info(weigh_station)
            weigh_station_location = GeoPoint(weigh_station.latitude, weigh_station.longitude)
            # Add this in temporarily for sorting. Never put into the datastore.
            # Could return it by adding to message_fields_schema if we thought the client would use it.
            weigh_station.distance_to_target = WeighStationTrackerApi.distance_between_geopoints(user_location, weigh_station_location)
            sorted_weigh_stations.append(weigh_station)
            
        if wslm.limit is None:
            wslm.limit = 30 

        sorted_weigh_stations.sort(key=lambda weigh_station: weigh_station.distance_to_target)
        wslm.weigh_stations = sorted_weigh_stations[:wslm.limit]
        return wslm

    
    @classmethod
    def distance_between_geopoints(cls, point1, point2):
        '''http://www.movable-type.co.uk/scripts/latlong.html'''
        lat1 = point1.latitude
        long1 = point1.longitude
        lat2 = point2.latitude
        long2 = point2.longitude
        R = 6371; # km
        dLat = math.radians(lat2-lat1);
        dLong = math.radians(long2-long1);
        lat1 = math.radians(lat1);
        lat2 = math.radians(lat2);
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLong/2) * math.sin(dLong/2) * math.cos(lat1) * math.cos(lat2); 
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)); 
        d = R * c;
        return d
    
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