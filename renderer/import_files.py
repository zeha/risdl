import logging
import sys

import sqlalchemy

from . import reader

def process_one(logger, db, docid):
    logger.info('processing %s', docid)

    doc = reader.readdoc(docid)

    sql = (
        "INSERT INTO document("
        + (", ".join([f"\"{f}\"" for f in doc.keys()]))
        + ") VALUES ("
        + (", ".join([f"%({f})s" for f in doc.keys()]))
        + ")"
    )

    with db.begin():
        db.execute(sql, **doc)


def run():
    logger = logging.getLogger(__name__)
    with open('bundesnormen.index', 'r') as fp:
        idx = [l.strip() for l in fp.readlines() if l.startswith('NOR')]

    engine = sqlalchemy.create_engine('postgresql:///')
    db = engine.connect()
    errors = 0
    done = 0

    with db.begin():
        db.execute("CREATE TABLE document (id BIGSERIAL PRIMARY KEY, "
                   + (", ".join([f"\"{f}\" date" for f in reader.DATE_KEYS])) + " , "
                   + (", ".join([f"\"{f}\" text" for f in reader.META_KEYS])) + " , "
                   + (", ".join([f"\"{f}\" text" for f in reader.TEXT_KEYS]))
                   + ")")
        db.execute("CREATE INDEX idx_document_docid ON document(docid)")

    for fn in idx:
        docid = fn.split('.xml')[0]
        try:
            process_one(logger, db, docid)
            done += 1
        except Exception:
            logger.exception('FAIL')
            errors += 1

        if errors >= 100:
            break

    print("done", done, "errors", errors)

    return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format='%(asctime)s %(levelname)s %(message)s')
    run()
