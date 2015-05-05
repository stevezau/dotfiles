from __future__ import unicode_literals, division, absolute_import
import logging
from ftplib import FTP_TLS, FTP


from flexget import plugin
from flexget.event import event

log = logging.getLogger('ftp_command')


class PluginFtpCommand(object):

    schema = {
        'type': 'object',
        'properties': {
            'hostname': {'type': 'string'},
            'ssl': {'type': 'boolean'},
            'port': {'type': 'integer'},
            'command': {'type': 'string'},
            'username': {'type': 'string'},
            'password': {'type': 'string'},
        },
        'required': ['hostname', 'port', 'username', 'password'],
        'additionalProperties': False
    }

    def prepare_config(self, config):
        if isinstance(config, bool):
            config = {'enabled': config}
        config.setdefault('enabled', True)
        config.setdefault('tag', None)
        config.setdefault('ssl', False)
        config.setdefault('delete', False)

        return config

    def _connect_ftp(self, hostname, port, username, password, ssl=False, timeout=30):
        if ssl:
            ftp_client = FTP_TLS()
        else:
            ftp_client = FTP()

        ftp_client.connect(hostname, port, timeout=timeout)
        ftp_client.login(username, password)
        return ftp_client

    @plugin.priority(250)
    def on_task_output(self, task, config):
        config = self.prepare_config(config)

        if not config.get("enabled"):
            return

        try:
            ftp_client = self._connect_ftp(
                config['hostname'], config['port'],
                config['username'], config['password'], ssl=config['ssl']
            )
        except Exception as e:
            raise plugin.PluginError('unable to connect to ftp due to %s' % str(e))

        try:

            for entry in task.accepted:
                # Get ftp_command to send..
                if config.get("command"):
                    command = config['command']
                else:
                    command = entry.get('ftp_command')

                if command:
                    ftp_client.sendcmd(command)
                    log.info("Sent %s to ftp" % command)

        except Exception as e:
            raise plugin.PluginError('error sending command to ftp due to %s' % str(e))
        finally:
            ftp_client.close()


@event('plugin.register')
def register_plugin():
    plugin.register(PluginFtpCommand, 'ftp_command', api_ver=2)