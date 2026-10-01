"""Analysis download only. Does not override the Frappe DocType exporter."""
import csv
import io
import frappe
from rpm_worklog.analysis import dataset, COLUMNS


def safe_text(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def serialize(data, file_type):
    if file_type == 'CSV':
        stream = io.StringIO(newline='')
        writer = csv.writer(stream)
        writer.writerow(COLUMNS)
        for row in data['rows']:
            writer.writerow([safe_text(row[key]) for key in COLUMNS])
        return b'\xef\xbb\xbf' + stream.getvalue().encode('utf-8')
    from openpyxl import Workbook
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet('Worklog Analysis')
    sheet.append(list(COLUMNS))
    from openpyxl.cell import WriteOnlyCell
    for row in data['rows']:
        cells=[]
        for key in COLUMNS:
            value=row[key]
            if isinstance(value,str):
                cell=WriteOnlyCell(sheet,value=value)
                cell.data_type='s'  # Preserve literal text, never spreadsheet formulas.
                cells.append(cell)
            else:
                cells.append(value)
        sheet.append(cells)
    output=io.BytesIO()
    workbook.save(output)
    return output.getvalue()


@frappe.whitelist()
def download(scope='Self',filters=None,file_type='CSV'):
    if file_type not in ('CSV','XLSX'):
        frappe.throw('Choose CSV or XLSX')
    # One database request/transaction, not a series of paginated browser requests.
    data=dataset(scope,filters,complete=True)
    frappe.local.response.update({
        'type':'binary','filename':'worklog-analysis.'+file_type.lower(),
        'filecontent':serialize(data,file_type),
        'content_type':'text/csv; charset=utf-8' if file_type=='CSV' else
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'display_content_as':'attachment'})
