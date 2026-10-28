"""Download the cited primary paper and render its complete table/curve pages, read-only."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
out=Path('D:/STGPlanner/codex/outputs/gbp2_optimization_20261028/paper_review')
out.mkdir(exist_ok=True)
url='https://arxiv.org/pdf/2412.13664v4'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
pdf=out/'STGPlanner_2412.13664v4.pdf'
if pdf.exists():
    raw=pdf.read_bytes()
else:
    with opener.open(urllib.request.Request(url,headers={'User-Agent':'STGPlanner-research-review'}),timeout=40) as response:
        raw=response.read()
    pdf.write_bytes(raw)
assert raw.startswith(b'%PDF')
poppler=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
for number,label in [(5,'paper_page5_table'),(6,'paper_page6_curves')]:
    assert not (out/(label+'.png')).exists()
    subprocess.run([str(poppler),'-f',str(number),'-l',str(number),'-singlefile','-r','150','-png',str(pdf),str(out/label)],check=True)
(out/'source.json').write_text(json.dumps({'url':url,'pdf_sha256':hashlib.sha256(raw).hexdigest(),
    'rendered_physical_pages':[5,6],'scope':'Primary-paper TableI, method/sample-size context and Fig5 curves reviewed visually. Curves are not raw numerical author data.'},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'source_pdf':str(pdf),'bytes':len(raw),'rendered_pages':[5,6]}))
