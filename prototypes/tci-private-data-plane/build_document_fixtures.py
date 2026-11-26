"""Fictional labelled evidence in representative passive formats; no real business material."""
import json,pathlib,zipfile,hashlib
from docx import Document
from docx.shared import Inches,Pt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape,letter
from reportlab.lib import colors
root=pathlib.Path(__file__).parent;out=root/"document-fixtures";out.mkdir(exist_ok=True)
fixtures=json.loads((root/"golden-fixtures.json").read_text())["fixtures"]
schema=json.loads((root/"extraction-schema.json").read_text())["rules"]
selected={"Q01","Q05","Q09","Q13","Q17","Q21","Q26"};manifest=[]
for f in fixtures:
 id=f["criterionId"]
 if id not in selected:continue
 rule=next(r for r in schema if r["criterionId"]==id)
 pairs=list(zip([x["label"] for x in rule["fields"]],[x["value"] for x in f["expected"]]))
 pdf=out/(id+".pdf");c=canvas.Canvas(str(pdf),pagesize=landscape(letter),pageCompression=1)
 c.setTitle("Synthetic evidence fixture "+id);c.setFont("Helvetica-Bold",15);c.setFillColor(colors.HexColor("#0F2744"));c.drawString(38,565,"Synthetic evidence record "+id)
 c.setFont("Helvetica",10);c.setFillColor(colors.black);c.drawString(38,540,"Fictional labelled test data - not an assessment")
 y=510
 for label,value in pairs:c.drawString(38,y,f"{label}: {value}");y-=30
 c.save()
 doc=Document();doc.sections[0].left_margin=Inches(.8);doc.sections[0].right_margin=Inches(.8);doc.add_heading("Synthetic evidence record "+id,0);doc.add_paragraph("Fictional labelled test data. Not an assessment.")
 t=doc.add_table(rows=1,cols=2);t.style="Light Shading Accent 1";t.rows[0].cells[0].text="Field";t.rows[0].cells[1].text="Value"
 for label,value in pairs:
  row=t.add_row();row.cells[0].text=label;row.cells[1].text=value
 doc.save(out/(id+".docx"))
 for ext,location in [("pdf",lambda i:f"PDF page 1, extracted line {i+3}"),("docx",lambda i:f"Table 1, row {i+2}, cell 2"),("xlsx",lambda i:f"Sheet Evidence!B{i+3}")]:
  manifest.append({"filename":id+"."+ext,"criterionId":id,"requestId":f["requestId"],"expected":[{"key":x["key"],"value":x["value"],"location":location(i)} for i,x in enumerate(f["expected"])]})
(root/"golden-document-fixtures.json").write_text(json.dumps({"version":"0.2.0-alpha.2","scope":"21 entirely fictional labelled-format fixtures crossing seven dimensions; no free-form semantic claims","fixtures":manifest},ensure_ascii=False,indent=2)+"\n")
