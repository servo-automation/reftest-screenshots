#!/usr/bin/python
from PIL import Image
from flask import Flask, Response, request
from io import BytesIO
from pyvirtualdisplay import Display
from selenium.webdriver import Chrome
from threading import Lock

import contextlib, json, os, time, urllib2

SCRIPT = '''
<script>
var content = %r;

setTimeout(function() {
  process_log(content);
  show_images(0);
  show_differences({"checked": true});
  document.getElementById("images").removeChild(document.getElementById("imgcontrols"));
}, 500);
</script>
'''

class Driver(object):
    def __init__(self):
        self.lock = Lock()
        print 'Starting driver...'
        self.driver = Chrome()
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1280, 720)

    def take_shot(self, url, png):
        with self.lock:
            self.driver.get(url)
            time.sleep(1000)        # delay for javascript
            self.driver.get_screenshot_as_file(png)


display = Display(visible=0, size=(1280, 720))
display.start()
engine = Driver()
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

    with contextlib.closing(urllib2.urlopen(summary_url)) as fd_sum, contextlib.closing(urllib2.urlopen(log_url)) as fd_log:
        fails = map(lambda s: json.loads(s)['test'], filter(lambda s: '"status": "FAIL"' in s, fd_sum.read().split('\n')))
        result = filter(lambda s: 'screenshot' in s and any(f in s for f in fails), fd_log.read().split('\n'))
        if not result:
            return 'null'

    text = result[0]

    analyzer = 'http://hoppipolla.co.uk/410/reftest-analyser-structured.xhtml'
    modified = 'loaded_%s.xhtml' % build
    with contextlib.closing(urllib2.urlopen(analyzer)) as fd, open(modified, 'w') as out:
        html = fd.read()
        match = '</body>'
        idx = html.find(match)
        html = html[:idx] + SCRIPT % text + html[idx:]
        out.write(html)
        print 'Modified analyzer.'

    engine.take_shot('file://' + os.path.abspath(modified),
                     'result_%s.png' % build)

    elem = engine.driver.find_element_by_id('svg')
    size, pos = elem.size, elem.location
    img = Image.open(png)
    cropped = img.crop((pos['x'], pos['y'], pos['x'] + size['width'], pos['y'] + size['height']))
    byte_arr = BytesIO()
    cropped.save(byte_arr, format='PNG')
    os.remove(png)
    os.remove(modified)

    return Response(byte_arr.getvalue(), mimetype="image/png")


port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=True)
