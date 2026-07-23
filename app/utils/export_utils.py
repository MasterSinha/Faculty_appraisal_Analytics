import csv
from io import BytesIO, StringIO
from typing import Iterable, Mapping

from openpyxl import Workbook


def rows_to_csv(rows: Iterable[Mapping[str, object]]) -> bytes:
    rows = list(rows)
    output = StringIO()
    fieldnames = list(rows[0].keys()) if rows else ["message"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    if rows:
        writer.writerows(rows)
    else:
        writer.writerow({"message": "No records found"})
    return output.getvalue().encode("utf-8")


def rows_to_xlsx(rows: Iterable[Mapping[str, object]]) -> bytes:
    rows = list(rows)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Research Analytics"
    fieldnames = list(rows[0].keys()) if rows else ["message"]
    sheet.append(fieldnames)
    if rows:
        for row in rows:
            sheet.append([row.get(field) for field in fieldnames])
    else:
        sheet.append(["No records found"])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()

