from itertools import islice

import pymongo

from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.template.defaultfilters import truncatewords

from billy.models import db
from billy.utils import get_domain


def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))


class GenericListFeed(Feed):

    def get_object(self, request, **kwargs):
        try:
            collection = getattr(db, kwargs['collection_name'])
        except KeyError:
            collection = getattr(db, self.collection_name)

        try:
            obj = collection.find_one(kwargs['_id'])
        except KeyError:
            obj = collection.find_one(kwargs['abbr'])

        if obj is None:
            raise FeedDoesNotExist
        return obj

    def link(self, obj):
        return obj.get_absolute_url()

    def items(self, obj):
        attr = getattr(obj, self.query_attribute)
        if callable(attr):
            kwargs = {'limit': 100}
            sort = getattr(self, 'sort', None)
            if sort is not None:
                kwargs['sort'] = sort
            return attr(**kwargs)
        else:
            return attr


class VotesListFeed(GenericListFeed):
    collection_name = 'legislators'
    query_attribute = 'votes_manager'
    sort = [('date', pymongo.DESCENDING)]

    def title(self, obj):
        s = u"{0}: Votes by {1}."
        return s.format(get_domain(), obj.display_name())

    description = title

    def item_description(self, item):
        template = u'''
        <b>motion:</b> {0}</br>
        <b>bill description:</b> {1}
        '''
        return template.format(item['motion'], item.bill()['title'])

    def item_title(self, item):
        return '%s (%s)' % (
            item.bill()['bill_id'],
            item['date'].strftime('%B %d, %Y'))
