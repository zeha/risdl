#!/bin/bash

# page=100

# curl https://data.bka.gv.at/ris/api/v2.5/bundesnormen -XPOST \
#     -H 'Content-Type: application/json' \
#     -d '@-' \
#     << EOT
# {"BundesnormenSearchRequest": {
#   "Fassung": {"FassungVom": "2020-07-20"},
#   "DokumenteProSeite": "OneHundred",
#   "Seitennummer": "${page}"
# }}
# EOT
#           <!-- NOR12024408  -->
#            <Fassung><FassungVom>2020-07-20</FassungVom></Fassung>

page=1

while true; do

echo "index page $page ..."

curl -XPOST \
    -H 'SOAPAction: "http://ris.bka.gv.at/ogd/V2_5/SearchDocuments"' \
    -H 'Content-Type: text/xml; charset=utf-8' \
    -d '@-' \
    http://data.bka.gv.at//ris/ogd/v2.5/ogdrisservice.asmx \
    > bundesnormen/index-${page}.xml \
    << EOT
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SearchDocuments xmlns="http://ris.bka.gv.at/ogd/V2_5">
      <query>
        <Suche>
          <Bundesnormen>
            <DokumenteProSeite>OneHundred</DokumenteProSeite>
            <Seitennummer>${page}</Seitennummer>
          </Bundesnormen>
        </Suche>
      </query>
    </SearchDocuments>
  </soap:Body>
</soap:Envelope>
EOT

if grep 'Die Seitennummer' bundesnormen/index-${page}.xml; then
  break
fi

for url in $(xmllint bundesnormen/index-1.xml --format | awk '/<Url>(.*\.xml)</ { FS=">"; $0=$2; print $1; }' | sed -e 's!<.*!!');
do
  (cd bundesnormen; curl -O "$url")
done

page=$((page+1))

break

done
