#!/usr/bin/python
from PIL import Image
from flask import Flask, Response, request
from io import BytesIO
from pyvirtualdisplay import Display
from selenium.webdriver.chrome.options import Options

import contextlib, json, os, urllib2

display = Display(visible=0, size=(1280, 720))
display.start()
app = Flask(__name__)

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

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    if os.environ.get('GOOGLE_CHROME_PATH'):
        chrome_options.binary_location = os.environ['GOOGLE_CHROME_PATH']
    print 'Starting driver...'
    driver = Chrome(chrome_options=chrome_options)
    driver.set_window_position(0, 0)
    driver.set_window_size(1280, 720)
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

    driver.get('file://' + os.path.abspath(modified))
    png = 'result_%s.png' % build
    driver.get_screenshot_as_file(png)

    elem = driver.find_element_by_id('svg')
    size, pos = elem.size, elem.location
    img = Image.open(png)
    cropped = img.crop((pos['x'], pos['y'], pos['x'] + size['width'], pos['y'] + size['height']))
    byte_arr = BytesIO()
    cropped.save(byte_arr, format='PNG')
    driver.quit()
    os.remove(png)
    os.remove(modified)

    return Response(byte_arr.getvalue(), mimetype="image/png")


port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=True)
