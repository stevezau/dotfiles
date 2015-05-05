from __future__ import unicode_literals, division, absolute_import
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, Unicode, DateTime, PickleType, Index

from flexget.utils.database import safe_pickle_synonym
from flexget import db_schema, plugin
from flexget.event import event

log = logging.getLogger('track_entry')

Base = db_schema.versioned_base('track_entry', 0)


class TrackEntry(Base):

    __tablename__ = 'track_entry'
    __table_args__ = (Index('ix_torrent_title_url_tag', 'title', 'url', 'tag'),)

    id = Column(Integer, primary_key=True)
    title = Column(Unicode, index=True)
    url = Column(Unicode, index=True)
    tag = Column(Unicode, index=True)
    state = Column(Unicode, index=True)
    updated = Column(DateTime, index=True)
    _entry = Column('entry', PickleType)
    entry = safe_pickle_synonym('_entry')

    def __init__(self):
        self.added = datetime.now()

    def __str__(self):
        return '<Tracker(title=%s,url=%s,tag=%s,state=%s,updated=%s)>' %\
               (self.title, self.url, self.tag, self.state, self.updated.strftime('%Y-%m-%d %H:%M'))


class TrackEntryPlugin(object):

    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'delete': {'type': 'boolean'},
                    'state': {'type': 'string'},
                    'tag': {'type': 'string'},
                    'category': {'type': 'string'},
                },
                'required': ['state'],
                'additionalProperties': False
            }
        ]
    }

    def prepare_config(self, config):
        if isinstance(config, bool):
            config = {'enabled': config}
        config.setdefault('enabled', True)
        config.setdefault('tag', None)
        config.setdefault('delete', False)

        return config

    def on_task_learn(self, task, config):
        """Add new entries into archive. We use learn phase in case the task corrects title or url via some plugins."""
        config = self.prepare_config(config)
        if not config.get("enabled"):
            return

        for entry in task.accepted:
            track_entry = task.session.query(TrackEntry).filter(TrackEntry.title == entry['title']).filter(TrackEntry.url == entry['url']).first()

            if config.get("delete"):
                if track_entry:
                    task.session.delete(track_entry)
                return

            if not track_entry:
                track_entry = TrackEntry()
                track_entry.title = entry['title']
                track_entry.url = entry['url']
                if 'description' in entry:
                    track_entry.description = entry['description']

            if config.get("tag") is not None:
                track_entry.tag = config["tag"]
            if config.get("state") is not None:
                track_entry.state = config["state"]

            track_entry.entry = entry
            track_entry.updated = datetime.now()

            log.debug('Adding `%s` to entry' % (track_entry))

            task.session.add(track_entry)

    def on_task_abort(self, task, config):
        """
        Track even on task abort, except if the abort has happened before session
        was started.
        """
        if task.session is not None:
            self.on_task_learn(task, config)


@event('plugin.register')
def register_plugin():
    plugin.register(TrackEntryPlugin, 'track_entry', api_ver=2)
