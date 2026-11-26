import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const wb=Workbook.create(),s=wb.worksheets.add('Evidence');
s.getRange('A1:B3').values=[['Field','Value'],['Investment amount',1250],['Cost basis',null]];
s.getRange('B2').setNumberFormat('"SGD " #,##0.00');s.getRange('B3').formulas=[['=1+1']];
wb.recalculate();await (await SpreadsheetFile.exportXlsx(wb)).save('numeric-formula-fixture.xlsx');
