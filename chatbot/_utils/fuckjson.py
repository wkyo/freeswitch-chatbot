# -*- coding: utf-8 -*-
# convert unicode string in json to native encoding (utf-8)

import json


def json_hook_utf8(obj):
    # fuck python2 json
    return {k.encode('utf-8') if isinstance(k, unicode) else k: v.encode('utf-8') if isinstance(v, unicode) else v for k, v in obj}


def load(fp, *args, **kw):
    return json.load(fp, *args, object_pairs_hook=json_hook_utf8, **kw)


def loads(s, *args, **kw):
    return json.loads(s, *args, object_pairs_hook=json_hook_utf8, **kw)


dump = json.dump
dumps = json.dumps
