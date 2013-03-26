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
            newval = map(self.prepId, newval.split("/"))

            # likely, an initial "/" was not in the SNMP location. Check. Add if needed:
            if newval[0] != "/":
                # extra "" at beginning of list will add a "/" when joined:
                newval = "" + newval
            
            # Additional processing for RackSlot-related stuff begins here:

            # set extra to anything after a trailing "-" in the location name, and strip
            # the "-*" from the end of the location. This is used to hold RU location, such
            # as "Albuquerque/DC1/Rack01-25" -> "Albuquerque/DC1/Rack01" (ru=25).


            extra = ""
            seperator = newval[-1].find('-')
            if seperator != -1:
                newval[-1] = newval[-1][:seperator]
                extra = newval[-1][seperator+1:] 

            # rackSlot processing. In many cases below, I use [:x] or [x:y]
            # indexes to avoid throwing an IndexError exception if extra is ""
            # or only one character:

            if extra[:1].isdigit():
                # FOO-25: normal equipment on front of rack in position 25.
                rackSlot="rh=1,ru="+extra
            elif extra[:1] in ('r', 'R') and extra[1:].isdigit():
                # FOO-r25: normal equipment on rear of rack in position 25.
                rackSlot="rh=1,split=rear,ru="+extra[1:]
            elif extra[:1] in ('r', 'R') and extra[1:2] in ('l', 'L', 'r', 'R'):
                # ru position is not supported for these:
                if extra[1:2] in ('l', 'L'):
                    # FOO-rl: equipment on rear of rack on left side.
                    rackSlot = "split=left/rear"
                else:
                    # FOO-rr: equipment on rear of rack on right side.
                    rackSlot = "split=right/rear"
            elif len(extra) == 1 and extra[0] in ('r', 'R', 'l', 'L'):
                    if extra[0] in ('l', 'L'):
                        # FOO-l: equipment on left side of rack.
                        rackSlot="split=left"
                    else:
                        # FOO-r: equipment on right side of rack.
                        rackSlot="split=right" 
            else:
                rackSlot = ""

            location = "/".join(newval)
            
            # At this point, location is set to the new SNMP Zenoss-friendly location string
            # and rackSlot has been initialized to a value as necessary.

            # Behind the scenes, we only want rackSlot to be initialized to a value if the
            # location has changed.
            
            # TODO

            om.setSNMPLocation = "/".join(newval)

        log.info('Location: %s', om.setSNMPLocation)

        return om

# vim: set ts=4 sw=4 expandtab: 
