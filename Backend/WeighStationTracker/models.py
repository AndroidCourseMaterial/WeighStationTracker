'''
Created on Dec 2, 2013

See http://www.coopsareopen.com/indiana-weigh-stations.html or http://www.dieselboss.com/truckstops.asp for an example.

Also, https://play.google.com/store/apps/details?id=com.leighgagnon.WeighStations&hl=en

@author: Dave Fisher and Matt Boutell
'''
from endpoints_proto_datastore.ndb.model import EndpointsModel
from google.appengine.ext import ndb



class WeighStation(EndpointsModel):
    _message_fields_schema = ('id', 'name', 'latitude', 'longitude', 'state', 'route', 'mile_marker', 'location_description')
    name = ndb.StringProperty()
    latitude = ndb.FloatProperty()
    longitude = ndb.FloatProperty()
    state = ndb.StringProperty()
    route = ndb.StringProperty()
    mile_marker = ndb.FloatProperty()
    location_description = ndb.StringProperty()
    last_touch_date_time = ndb.DateTimeProperty(auto_now=True)    

class WeighStationStatus(EndpointsModel):
    _message_fields_schema = ('id', 'weigh_station_id', 'email', 'status', 'last_touch_date_time')
    weigh_station_id = ndb.IntegerProperty()
    email = ndb.StringProperty()
    status = ndb.StringProperty()
    last_touch_date_time = ndb.DateTimeProperty(auto_now=True)    
    