from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import plugin
from flexget.event import event

log = logging.getLogger('set_config')


class PluginPathSelect(object):
    """ Set rtorrent server depending on path """

    @plugin.priority(250)
    def on_task_output(self, task, config):
        if "rtorrent" in task.config:
            if task.config['rtorrent']['directory'].startswith("/data/north"):
                task.config['rtorrent']['uri'] = "scgi://192.168.0.210:5000"
            if task.config['rtorrent']['directory'].startswith("/data/south"):
                task.config['rtorrent']['uri'] = "scgi://192.168.0.200:5000"


@event('plugin.register')
def register_plugin():
    plugin.register(PluginPathSelect, 'set_config', api_ver=2)