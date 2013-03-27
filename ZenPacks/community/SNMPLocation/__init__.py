import logging
log = logging.getLogger('zen.SNMPLocation')

import Globals

from Products.ZenModel.Device import Device
from Products.ZenUtils.Utils import unused, monkeypatch
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase

unused(Globals)

# To use the SNMP Location data to update the device, we need *two* methods.
# They are setSNMPLocation() and getSNMPLocation(), and they must begin with
# the "get" and "set" prefix. Monkey patching is used to add them to the
# base Device object in Zenoss, which is the right thing to do because we
# want this functionality enabled for *all* devices in Zenoss.

# This code works in conjunction with the collector/modeler plugin defined
# in modeler/plugins/community/snmp/LocationMap.py. The two methods below
# need to exist for the modeler plugin to update the device objects properly.

# Here is how these two methods work. Our modeler plugin will get a new
# SNMP location value, and it will place this value in an objectMap.

# Zenoss will compare the value placed in the objectMap with the return value
# of getSNMPLocation() call.
 
# Zenoss will see if the values match. If they do, no action will be taken as
# the object will be considered to already have this value applied.

# However, if the values don't match, then device.setSNMPLocation(newvalue)
# will be called which will take care of updating the object.

@monkeypatch("Products.ZenModel.Device.Device")
def setSNMPLocation(self, location):
    self.setLocation(location)
    
@monkeypatch("Products.ZenModel.Device.Device")
def getSNMPLocation(self):
    
    loc = self.getLocationName()

    # getLocationName() will return an empty string if the device isn't in
    # a location. Otherwise, it will return the fully-qualified location,
    # with each organizer separated by a "/". The location, if set, will 
    # also have an initial "/".

    # The collector plugin takes care of "tweaking" the location value
    # receieved from SNMP so that it is Zenoss-friendly (no illegal characters)
    # and will match the format returned by getLocationName().

    return loc

# Below, we create a sub-class of the ZenPack object which will be used to 
# install and remove this ZenPack. This allows us to automatically add our
# modeler plugin to the base device class. We will also automatically remove
# this modeler plugin from the base device class if this ZenPack is removed:

class ZenPack(ZenPackBase):

    # List of modeler plugins that we will automatically enable:

    modeler_plugins = [ 'community.snmp.LocationMap' ]

    def devices_or_classes_to_modify_iterator(self, app):
    
    # This method returns an iterator of device classes and devices on which we
    # will auto-enable and auto- disable on modeler plugin on install/removal
    # of this ZenPack.

    # This method returns the root device class plus all devices and device classes
    # with overridden modeler plugin settings. This has the effect of enabling/
    # disabling it globally:

        yield app.zport.dmd.Devices.getOrganizer('/')
        for x in app.zport.dmd.Devices.getOverriddenObjects('zCollectorPlugins'):
            yield x

    def add_plugin_to_device_or_class(self, d, plugin):
        """Add a modeler plugin to a particular device or device class."""
        plugins = list(d.zCollectorPlugins)
        if plugin not in plugins:
            log.info('Adding %s modeler plugin to %s', plugin, d.id)
            plugins.append(plugin)
            d.setZenProperty('zCollectorPlugins', plugins)

    def remove_plugin_from_device_or_class(self, d, plugin):
        """Remove a modeler plugin from a particular device or device class"""
        plugins = list(d.zCollectorPlugins)
        if plugin in plugins:
            log.info('Removing %s modeler plugin from %s', plugin, d.id)
            plugins.remove(plugin)
            d.setZenProperty('zCollectorPlugins', plugins)

    def enable_modeler_plugins(self, dmd, myplugin_iter, mydev_iter):
        """Enable modeler plugin(s) (main method)"""
        for plugin in myplugin_iter:
            for d in mydev_iter:
                # Only add if SNMP monitoring is enabled:
                if not d.zSnmpMonitorIgnore:
                    self.add_plugin_to_device_or_class(d, plugin)
 
    def disable_modeler_plugins(self, dmd, myplugin_iter, mydev_iter):
        """Disable modeler plugin(s) (main method)"""
        for plugin in myplugin_iter:
            for d in mydev_iter:
                self.remove_plugin_from_device_or_class(d, plugin)

    # Methods called when ZenPack is installed and removed:

    def install(self, app):
        ZenPackBase.install(self, app)
        # enable globally, for all device classes and devices:
        self.enable_modeler_plugins( app.zport.dmd, self.modeler_plugins, self.devices_or_classes_to_modify_iterator(app) )

    def remove(self, app, leaveObjects=False):
        # disable globally, for all device classes and devices:
        self.disable_modeler_plugins(app.zport.dmd, self.modeler_plugins, self.devices_or_classes_to_modify_iterator(app) )
        ZenPackBase.remove(self, app, leaveObjects=leaveObjects)

# vim: set ts=4 sw=4 expandtab: 
