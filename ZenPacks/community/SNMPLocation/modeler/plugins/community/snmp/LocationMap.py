from Products.DataCollector.plugins.CollectorPlugin import SnmpPlugin, GetMap

class LocationMap(SnmpPlugin):
    
    maptype = "LocationMap"

    snmpGetMap = GetMap({ '.1.3.6.1.2.1.1.6.0' : 'setSNMPLocation' })
    
    def process(self, device, results, log):

        """Collect SNMP location information from this device"""

        log.info('processing %s for device %s', self.name(), device.id)

        getdata, tabledata = results
        om = self.objectMap(getdata)

        # Now it's time to place our SNMP location value inside an objectMap.
        # Zenoss will use this objectMap to "imprint" any necessary value
        # changes to the underlying device object.  Specifically, our new SNMP
        # value will interface with our getSNMPLocation() and setSNMPLocation()
        # methods on the underlying device. 

        # We won't hand back the raw location value received from SNMP,
        # however. Instead, we will tweak the value somehwat:
        
        # prepId() will be used to convert illegal device/organizer characters
        # to underscores. But we will preserve any '/' characters (also
        # considered illegal in location organizer names) since our methods use
        # them as a means to specify a heirarchy of location organizers.

        # We will also prepend a "/" to the string if it not blank and doesn't
        # begin with a ".".
        
        # These changes will prepare the SNMP location value for acceptance by
        # our setSNMPLocation() method, and also ensure that if the SNMP value
        # has already been applied, that our tweaked SNMP string will match
        # that returned by getSNMPLocation(), to avoid unnecessary model
        # updates.

        newval = om.setSNMPLocation        
        if len(newval):
            # run prepId() on all parts between slashes:
            newval = "/".join(map(self.prepId, newval.split("/"))) 
            # likely, an initial "/" was not in the SNMP location. Check. Add if needed.
            if newval[0] != "/":
                newval = "/" + newval
            # update our objectMap with our tweaked value:
            om.setSNMPLocation = newval

        log.info('Location: %s', om.setSNMPLocation)

        return om

# vim: set ts=4 sw=4 expandtab: 
