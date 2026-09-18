"""Presentation only: never change Employee.name or ownership."""
FIELDS = ['name', 'last_name', 'first_name', 'employee_name', 'employee_number']


def label(row):
    name = ' '.join(str(row.get(key) or '').strip() for key in ('last_name','first_name')).strip()
    return f"{name or row.get('employee_name') or '未填姓名'} | {row.get('employee_number') or '未填工號'}"
