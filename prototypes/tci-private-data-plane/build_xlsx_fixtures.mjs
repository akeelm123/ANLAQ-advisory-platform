import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const data=JSON.parse(await fs.readFile('golden-fixtures.json','utf8')).fixtures;
const schema=JSON.parse(await fs.readFile('extraction-schema.json','utf8')).rules;
const ids=new Set(['Q01','Q05','Q09','Q13','Q17','Q21','Q26']);
for(const f of data.filter(f=>ids.has(f.criterionId))){
 const r=schema.find(r=>r.criterionId===f.criterionId);
 const wb=Workbook.create(),s=wb.worksheets.add('Evidence');s.showGridLines=false;
 const values=[['Synthetic evidence record '+f.criterionId,'Fictional test data'],['Field','Value'],...r.fields.map((x,i)=>[x.label,f.expected[i].value])];
 const all=s.getRangeByIndexes(0,0,values.length,2);all.values=values;all.format.wrapText=true;all.format.font.name='Arial';all.format.font.size=11;all.format.rowHeight=30;
 s.getRangeByIndexes(0,0,values.length,1).format.columnWidth=42;s.getRangeByIndexes(0,1,values.length,1).format.columnWidth=76;
 s.getRange('A1:B2').format.fill='#0F2744';s.getRange('A1:B2').format.font.color='#FFFFFF';s.getRange('A1:B2').format.font.bold=true;
 wb.recalculate();await (await SpreadsheetFile.exportXlsx(wb)).save('document-fixtures/'+f.criterionId+'.xlsx');
 if(f.criterionId==='Q01'){const b=await wb.render({sheetName:'Evidence',range:'A1:B7',format:'png'});await fs.writeFile('/tmp/tci-fixture-xlsx.png',new Uint8Array(await b.arrayBuffer()));}
}
