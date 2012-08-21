from google.appengine.ext import ndb

class AuditEntryModel(ndb.Model):
    """
    Definition of AuditEntry
    """
    requestTime = ndb.DateTimeProperty(indexed=True, name='rt')
    host        = ndb.StringProperty(indexed=False,  name='ht')
    path        = ndb.StringProperty(indexed=True,   name='pth')
    version     = ndb.StringProperty(indexed=False,  name='ver')
    queryStr    = ndb.StringProperty(indexed=False,  name='qry')
    method      = ndb.StringProperty(indexed=False,  name='me')
    status      = ndb.IntegerProperty(indexed=True,  name='st')
    duration    = ndb.FloatProperty(indexed=False,   name='dur')
    body        = ndb.BlobProperty(indexed=False,    name='bod')

    @classmethod
    def buildKey(cls, guid=None):
        """
        Builds an ndb.Key
        """
        if not guid:
            guid = uuid4().hex
        if isinstance(guid, UUID):
            guid = guid.hex
        return ndb.Key(cls, guid)

    @classmethod
    def lookupByPathAndDateRangeQuery(cls, path, start=None, end=None):
        """
        Returns a query for a audit entry path with an optional date range.
        """
        if not path:
            raise ValueError('path is required.')
        query = cls.query().filter(cls.path == path)
        if start:
            query = query.filter(cls.requestTime >= start)
        if end:
            query = query.filter(cls.requestTime < end)
        return query