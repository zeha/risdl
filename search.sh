curl -XPOST \
    -H 'SOAPAction: "http://ris.bka.gv.at/ogd/V2_5/GetDocNumbers"' \
    -H 'Content-Type: text/xml; charset=utf-8' \
    -d '@-' \
    http://data.bka.gv.at//ris/ogd/v2.5/ogdrisservice.asmx \
    << EOT
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetDocNumbers xmlns="http://ris.bka.gv.at/ogd/V2_5">
      <documentNumbers>
        <string>NOR12024408</string>
      </documentNumbers>
      <application>Bundesnormen</application>
    </GetDocNumbers>
  </soap:Body>
</soap:Envelope>
EOT

