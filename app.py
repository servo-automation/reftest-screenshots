#!/usr/bin/python
from PIL import Image
from StringIO import StringIO
from base64 import b64encode, b64decode
from flask import Flask, request
from io import BytesIO

import contextlib, json, os, urllib2

app = Flask(__name__)


@app.route("/")
def index():
    url = request.args.get("url", "")
    if not url:
        return 'null'

    summary_url = url + '/steps/test/logs/css-errorsummary.log/text'
    log_url = url + '/steps/test/logs/test-css.log/text'
    build = url.split('/')[-1]
    print summary_url
    print log_url

    with contextlib.closing(urllib2.urlopen(summary_url)) as fd_sum:
        fails = map(lambda s: json.loads(s)['test'],
                    filter(lambda s: '"status": "FAIL"' in s,
                           fd_sum.read().split('\n')))

    with contextlib.closing(urllib2.urlopen(log_url)) as fd_log:
        result = filter(lambda s: 'screenshot' in s and any(f in s for f in fails),
                        fd_log.read().split('\n'))
        if not result:
            return '{}'

    resp = []
    for res in result:
        res = json.loads(res)
        data = res['extra']['reftest_screenshots']
        test, ref = data[0], data[2]
        test_img = Image.open(BytesIO(b64decode(test['screenshot'])))
        ref_img = Image.open(BytesIO(b64decode(ref['screenshot'])))
        blend_img = Image.blend(test_img, ref_img, alpha=0.75)
        buf = BytesIO()
        blend_img.save(buf, format='PNG')

        resp.append({
            'test': {
                'url': test['url'],
                'image': test['screenshot']
            },
            'ref': {
                'url': ref['url'],
                'image': ref['screenshot']
            },
            'blend': b64encode(buf.getvalue()),
        })

    return app.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )


port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=True)
