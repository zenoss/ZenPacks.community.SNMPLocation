import Globals

from Products.ZenModel.Device import Device
from Products.ZenUtils.Utils import unused, monkeypatch
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase

unused(Globals)

# SNMPLocationCallback() is sent location data from the modeler plugin and can
# perform actions to update the device. Common operations would involve putting
# the device in an organizer based on the name of the SNMP location.
#
# Other actions could also be performed, such as initialization of the device's
# rackSlot value... or anything else.

@monkeypatch("Products.ZenModel.Device.Device")
def SNMPLocationCallback(self, location):
    self.setLocation(location)
    
    if self.rackSlot == "":
        self.rackSlot = "nifty"

# Below, we create a sub-class of the ZenPack object which will be used to 
# install and remove this ZenPack. This allows us to automatically add our
# modeler plugin to the base device class. We will also automatically remove
# this modeler plugin from the base device class if this ZenPack is removed:

class ZenPack(ZenPackBase):

    # List of modeler plugins that we will automatically enable:

    modeler_plugins = [ 'community.snmp.LocationMap' ]

    # Iterator of device classes and devices on which we will auto-enable and auto-
    # disable on modeler plugin on install/removal of this ZenPack.

    # This method returns the root device class plus all devices and device classes
    # with overridden modeler plugin settings. This has the effect of enabling/
    # disabling it globally:

    def devices_or_classes_to_modify_iterator(self):
        yield app.zport.dmd.Devices.getOrganizer('/')
        for x in app.zport.dmd.Devices.getOverriddenObjects('zCollectorPlugins'):
            yield x

    # Add a modeler plugin to a particular device or device class:

    def add_plugin_to_device_or_class(self, d, plugin):
        plugins = list(d.zCollectorPlugins)
        if plugin not in plugins:
            log.info('Adding %s modeler plugin to %s', plugin, d.id)
            plugins.append(plugin)
            d.setZenProperty('zCollectorPlugins', plugins)

    # Remove a modeler plugin from a particular device or device class:

    def remove_plugin_from_device_or_class(self, d, plugin):
        plugins = list(d.zCollectorPlugins)
        if plugin in plugins:
            log.info('Removing %s modeler plugin from %s', plugin, d.id)
            plugins.remove(plugin)
            dc.setZenProperty('zCollectorPlugins', plugins)

    # Enable modeler plugins (main method)

    def enable_modeler_plugins(self, dmd, myplugin_iter, mydev_iter):
        for plugin in myplugin_iter:
            for d in mydev_iter:
                # Only add if SNMP monitoring is enabled:
                if not d.zSnmpMonitorIgnore:
                    self.add_plugin_to_device_or_class(d, plugin)
   
    # Disable modeler plugins (main method)
 
    def disable_modeler_plugins(self, dmd, myplugin_iter, mydev_iter):
        for plugin in myplugin_iter:
            for d in mydev_iter:
                try:
                    dc = dmd.Devices.getOrganizer(d)
                except KeyError:
                    continue
                self.remove_plugin_from_device_or_class(d, plugin)

    # Methods called when ZenPack is installed and removed:

    def install(self, app):
        ZenPackBase.install(self, app)
        self.enable_modeler_plugins( app.zport.dmd, self.modeler_plugins, self.devices_or_classes_to_modify_iterator() )

    def remove(self, app, leaveObjects=False):
        self.remove_modeler_plugins(app.zport.dmd, self.modeler_plugins, self.devices_or_classes_to_modify_iterator() )
        ZenPackBase.remove(self, app, leaveObjects=leaveObjects)

# vim: set ts=4 sw=4 expandtab: 
