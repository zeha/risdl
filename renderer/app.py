from flask import Flask, request, redirect, url_for, render_template
import re
import html

from lxml import etree

from . import reader


app = Flask(__name__)


def _fix_leading_whitespace(s):
    s2 = s.lstrip()
    s2 = ('&nbsp;' * (len(s) - len(s2))) + s2
    return s2


@app.template_filter('render_text')
def rst_filter(s):
    if not s:
        return ''
    lines = s.splitlines()

    lines = [_fix_leading_whitespace(html.escape(line)) for line in lines]
    return '<br>\n'.join(lines)
    # return html.escape(s).replace('\n', '<br>')


@app.template_filter('repr')
def repr_filter(s):
    if not s:
        return ''
    return repr(s)


@app.route('/viewdoc')
def viewdoc():
    docid = request.values.get('docid', None)
    if docid:
        xmlstr = etree.tostring(reader.readxml(docid), pretty_print=True).decode('utf-8')
        data = reader.readdoc(docid)

        # md = markdown.Markdown()
        # main_text_html = md.convert(data['main_text'])

        return render_template('docview.html.jinja2', xmlstr=xmlstr, data=data,
                               date_keys=reader.DATE_KEYS,
                               meta_keys=reader.META_KEYS,
                               text_keys=reader.TEXT_KEYS)

    else:
        return redirect(url_for('.hello'))


@app.route('/')
def hello():
    return render_template('hello.html.jinja2')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
