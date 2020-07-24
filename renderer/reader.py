import datetime
import logging
import re
from typing import Dict

from lxml import etree

NS = '{http://www.bka.gv.at}'

# keys should be given in display order
DATE_KEYS = ['valid_from', 'valid_to', 'changedate', 'signingdate', 'entrydate']
DATE_DEFAULTS = {'DATE_KEYS': datetime.date.max}
TEXT_KEYS = ['cautonary_info_text', 'introduction_text', 'other_text', 'preamble_text', 'main_text',
             'ratification_text', 'note_text']
META_KEYS = ['docid', 'docid_old', 'lawid', 'type', 'part', 'catalogue', 'keywords', 'section',
             'source_initial', 'source_change', 'changed_by',
             'title', 'title_short', 'title_long', 'see_also', 'parties', 'languages', 'errors']
ALL_KEYS = META_KEYS + TEXT_KEYS + DATE_KEYS

ct_map = {
    'kurztitel': 'title',
    'langtitel': 'title_long',
    'gesnr': 'lawid',
    'doknr': 'docid',
    'adoknr': 'docid_old',
    'typ': 'type',
    'artikel_anlage': 'part',
    'ikra': 'valid_from',
    'akra': 'valid_to',
    'abkuerzung': 'title_short',
    'beachte': 'cautonary_info_text',
    'index': 'catalogue',
    'schlagworte': 'keywords',
    'geaendert': 'changedate',
    'promkleinlsatz': 'introduction_text',
    'unterzeichnungsdatum': 'signingdate',
    'aenderung': 'changed_by',
    'text': 'main_text',
    'prae_promul': 'preamble_text',
    'Sonstige textteile': 'other_text',
    'ratifikation': 'ratification_text',
    'anmerkung': 'note_text',
    'vertragsparteien': 'parties',
    'sprachen': 'languages',
}

_datetime_re = re.compile('^\d{2}\.\d{2}\.\d{4}')
_logger = logging.getLogger(__name__)


def _austrian_date_to_datetime(text, default=None):
    if text is None:
        return default
    tmp = text.split('.')
    return datetime.date(int(tmp[2]), int(tmp[1]), int(tmp[0]))


def _parse_sources(text):
    # "BGBl. II Nr. 197/2020 zuletzt geändert durch BGBl. II Nr. 287/2020"
    tmp = text.split(' zuletzt geändert durch ')
    return tmp[0], tmp[1] if len(tmp) > 1 else None


def _joined_text(elem):
    return ' '.join(list(elem.itertext()))


def readxml(docid) -> etree.Element:
    fn = f'{docid}.xml'
    h = sum([ord(y) for y in fn]) % 10
    p = f'bundesnormen/h/{h}/{fn}'
    with open(p, 'rb') as fp:
        xml = etree.XML(fp.read())

    return xml.find(f'{NS}nutzdaten').find(f'{NS}abschnitt')


def _startswith_numbered_list(text):
    try:
        tmp = text.split(' ')[0]
        if tmp[-1] == '.':
            int(tmp[0:-1])
            return True
    except:
        return False


def readdoc(docid) -> Dict:
    root = readxml(docid)
    data = {
    }

    first_main_text_para = True
    errors = 0

    for elem in root.iterchildren():
        if elem.tag == f'{NS}fzinhalt':
            continue
        if elem.tag == f'{NS}kzinhalt':
            if 'section' not in data:
                data['section'] = _joined_text(elem)
            continue

        if elem.tag == f'{NS}absatz' and elem.get('typ') in ('erltext', 'novao2'):
            ct = elem.get('ct')
            key = None
            mytext = _joined_text(elem)
            if ct is None:
                if _datetime_re.match(mytext):
                    # lots of docs do not have the dates marked.
                    if data.get('valid_from', None) is None:
                        data['valid_from'] = mytext
                        continue
                    elif data.get('valid_to', None) is None:
                        data['valid_to'] = mytext
                        continue
            elif ct == 'kundmachungsorgan':
                data['source_initial'], data['source_change'] = _parse_sources(mytext)
                continue
            elif ct == 'anmerkung':
                if _startswith_numbered_list(mytext):
                    mytext = mytext.split('. ', 1)[1]
                if mytext.startswith('Erfassungsstichtag:'):
                    key = 'entrydate'
                    mytext = mytext.split(':', 1)[1]
                elif mytext.startswith('vgl. ') or mytext.startswith('Vgl. '):
                    key = 'see_also'
                    mytext = mytext[5:]
                elif mytext.startswith('Zu dieser Rechtsvorschrift ist eine englische Übersetzung in der Applikation'):
                    continue

            if not key:
                key = ct_map.get(ct, None)

            if not key:
                _logger.error('cannot find key for %s - %s', ct, mytext)
                if ct is None:
                    errors += 1
                    continue
                raise KeyError(ct)
            data[key] = data.setdefault(key, '') + f'{mytext}\n'
            continue

        if elem.tag == f'{NS}ueberschrift' and elem.get('typ') == 'titel':
            # Header
            continue

        if ((elem.tag == f'{NS}ueberschrift' and elem.get('typ') == 'para') or
                (elem.tag == f'{NS}inhaltsvz' and elem.get('typ') == 'ueberschrift')):
            # print('ueberschrift for ct=', elem.get('ct'))
            mytext = _joined_text(elem)
            key = 'main_text'
            data[key] = data.setdefault(key, '') + f'{mytext}\n{"=" * len(mytext)}\n\n'
            continue

        if elem.tag == f'{NS}ueberschrift' and elem.get('typ') in ('art', 'anlage'):
            mytext = _joined_text(elem)
            key = ct_map[elem.get('ct')]
            data[key] = data.setdefault(key, '') + f'{mytext}\n{"-" * len(mytext)}\n\n'
            continue

        if elem.tag == f'{NS}table':
            mytext = _joined_text(elem)
            key = 'main_text'
            data[key] = data.setdefault(key, '') + f'{mytext}\n\n'
            continue

        if elem.tag == f'{NS}ueberschrift' and elem.get('typ') in ('g1min', 'g2', 'g1', 'erlz', 'erll'):
            mytext = _joined_text(elem)
            key = ct_map[elem.get('ct')]
            data[key] = data.setdefault(key, '') + f'{mytext}\n\n'
            continue

        if elem.tag == f'{NS}absatz' and elem.get('typ') == 'promkleinlsatz':
            mytext = _joined_text(elem)
            key = ct_map[elem.get('typ')]
            data[key] = data.setdefault(key, '') + f'{mytext}\n\n'
            continue

        if elem.tag == f'{NS}absatz' and elem.get('typ') == 'pre':
            mytext = _joined_text(elem)
            key = ct_map[elem.get('ct')]
            data[key] = data.setdefault(key, '') + f'  {mytext}\n'
            continue

        if elem.tag == f'{NS}abstand':
            key = ct_map.get(elem.get('ct'), None)
            if key:
                # we handle "kundmachungsorgan" and others specially for real text, but lets ignore it here.
                data[key] = data.setdefault(key, '') + '\n'
            continue

        if elem.tag == f'{NS}absatz' and elem.get('typ') == 'abs':
            ct = elem.get('ct')
            key = ct_map.get(ct, None)
            if not key:
                _logger.error('cannot find key for ct=%s in absatz!', ct)
                errors += 1
                raise KeyError(ct)
            if key == 'main_text':
                if first_main_text_para:
                    partsym = elem.find(f'{NS}gldsym')
                    if partsym is not None:
                        partsym_text = partsym.text.replace('\xa0', ' ')
                        if partsym_text == data['part'] or partsym_text == (data['part'] + '.'):
                            partsym_tail = partsym.tail
                            if partsym_tail:
                                partsym_tail = partsym_tail.strip()
                            if partsym_tail:
                                if elem.text:
                                    elem.text = partsym_tail + elem.text
                                else:
                                    elem.text = partsym_tail
                            elem.remove(partsym)
                            first_main_text_para = False

            mytext = _joined_text(elem)
            if ct:
                data[key] = data.setdefault(key, '') + f'{mytext}\n\n'
                continue
            else:
                raise ValueError('unhandled absatz of ct type %r' % ct)

        if elem.tag == f'{NS}absatz' and elem.get('typ') == 'abbobj':
            errors += 1
            _logger.error('Unimplemented absatz of typ "%s" in this document', elem.get('typ'))
            continue
        if elem.tag in (f'{NS}liste', f'{NS}abbobj', f'{NS}inhaltsvz'):
            errors += 1
            _logger.error('Unimplemented tag "%s" in this document', elem.tag)
            continue

        errors += 1
        _logger.error('unhandled tag: %s ct=%s typ=%s text=%s',
                      elem.tag, elem.get('ct', None), elem.get('typ', None), list(elem.itertext()))
        raise ValueError('unhandled tag: %s %s %s' % (elem.tag, elem.get('typ', None), list(elem.itertext())))

    for k, v in data.items():
        if v and isinstance(v, str):
            if not v:
                v = None
            data[k] = v

    for k in DATE_KEYS:
        data[k] = _austrian_date_to_datetime(data.get(k, None), DATE_DEFAULTS.get(k, None))

    for k in TEXT_KEYS:
        data.setdefault(k, None)

    for k in data.keys():
        if k not in ALL_KEYS:
            raise RuntimeError('unknown key %s produced with value %r' % (k, data[k]))

    for k in META_KEYS + TEXT_KEYS:
        if isinstance(data.get(k, None), str):
            data[k] = data[k].strip()

    for k in ('keywords', 'languages'):
        if data.setdefault(k, None):
            data[k] = [
                val.strip()
                for val in data[k].replace('\n', ' ').split(', ')
            ]

    for k in ('changed_by', ):
        if data.setdefault(k, None):
            data[k] = [
                val.strip()
                for val in data[k].strip().split('\n')
            ]

    data['errors'] = errors

    if not data.get('docid', None):
        data['docid'] = docid
    elif data['docid'] != docid:
        raise RuntimeError('docid as parsed mismatch: %r != %r' % (data['docid'], docid))

    return data
