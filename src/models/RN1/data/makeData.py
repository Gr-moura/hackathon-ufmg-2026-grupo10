#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile


NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


@dataclass(frozen=True)
class SheetExport:
	sheet_name: str
	header_row: int
	output_name: str


EXPORTS: tuple[SheetExport, ...] = (
	SheetExport("Resultados dos processos", 1, "resultados_dos_processos.csv"),
	SheetExport("Subsídios disponibilizados", 2, "subsidios_disponibilizados.csv"),
)


def repo_root() -> Path:
	return Path(__file__).resolve().parents[4]


def default_input_file() -> Path:
	return repo_root() / "data" / "Hackaton_Enter_Base_Candidatos.xlsx"


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Split the workbook sheets into separate CSV files.")
	parser.add_argument("--input", type=Path, default=default_input_file(), help="Path to the XLSX workbook.")
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=default_input_file().parent,
		help="Directory where the CSV files will be written.",
	)
	return parser.parse_args()


def col_to_index(cell_ref: str) -> int:
	match = re.match(r"([A-Z]+)", cell_ref)
	if not match:
		return 0

	index = 0
	for char in match.group(1):
		index = index * 26 + (ord(char) - 64)
	return index


def read_shared_strings(zip_file: ZipFile) -> list[str]:
	if "xl/sharedStrings.xml" not in zip_file.namelist():
		return []

	root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
	shared_strings: list[str] = []
	for shared_item in root.findall("a:si", NS):
		text_parts = [text_node.text or "" for text_node in shared_item.findall(".//a:t", NS)]
		shared_strings.append("".join(text_parts))
	return shared_strings


def read_workbook_sheets(zip_file: ZipFile) -> dict[str, str]:
	workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
	relationships = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
	relationship_map = {rel.attrib["Id"]: "xl/" + rel.attrib["Target"] for rel in relationships}

	sheet_targets: dict[str, str] = {}
	sheets_element = workbook.find("a:sheets", NS)
	if sheets_element is None:
		return sheet_targets

	for sheet in sheets_element:
		sheet_name = sheet.attrib["name"]
		sheet_target = relationship_map[sheet.attrib[REL_NS]]
		sheet_targets[sheet_name] = sheet_target
	return sheet_targets


def format_number(raw_value: str) -> str:
	try:
		return format(float(raw_value), ".15g")
	except (TypeError, ValueError):
		return raw_value


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
	cell_type = cell.attrib.get("t")
	value_element = cell.find("a:v", NS)

	if cell_type == "s" and value_element is not None and value_element.text is not None:
		return shared_strings[int(value_element.text)]

	if cell_type == "inlineStr":
		inline_texts = [text_node.text or "" for text_node in cell.findall(".//a:t", NS)]
		return "".join(inline_texts)

	if cell_type == "b" and value_element is not None and value_element.text is not None:
		return "TRUE" if value_element.text == "1" else "FALSE"

	if value_element is None or value_element.text is None:
		return ""

	return format_number(value_element.text)


def read_sheet_rows(zip_file: ZipFile, sheet_target: str, shared_strings: list[str]) -> list[dict[int, str]]:
	root = ET.fromstring(zip_file.read(sheet_target))
	rows: list[dict[int, str]] = []

	for row_element in root.findall(".//a:sheetData/a:row", NS):
		row_values: dict[int, str] = {}
		for cell in row_element.findall("a:c", NS):
			column_index = col_to_index(cell.attrib["r"])
			if column_index:
				row_values[column_index] = read_cell_value(cell, shared_strings)
		rows.append(row_values)

	return rows


def sheet_to_csv_rows(rows: list[dict[int, str]], header_row: int) -> list[list[str]]:
	if header_row < 1 or header_row > len(rows):
		raise ValueError(f"Header row {header_row} is not available in the sheet.")

	max_column = max((max(row.keys(), default=0) for row in rows), default=0)
	if max_column == 0:
		return []

	header_values = rows[header_row - 1]
	header = [header_values.get(column_index, "") for column_index in range(1, max_column + 1)]

	data_rows: list[list[str]] = [header]
	for row_index in range(header_row, len(rows)):
		row_values = rows[row_index]
		normalized_row = [row_values.get(column_index, "") for column_index in range(1, max_column + 1)]
		if any(value != "" for value in normalized_row):
			data_rows.append(normalized_row)

	return data_rows


def write_csv(output_path: Path, rows: Iterable[Iterable[str]]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
		writer = csv.writer(csv_file)
		writer.writerows(rows)


def main() -> int:
	args = parse_args()
	input_file = args.input
	output_dir = args.output_dir

	if not input_file.exists():
		print(f"Input workbook not found: {input_file}", file=sys.stderr)
		return 1

	if input_file.suffix.lower() != ".xlsx":
		print("This script expects an .xlsx workbook.", file=sys.stderr)
		return 1

	with ZipFile(input_file) as zip_file:
		shared_strings = read_shared_strings(zip_file)
		sheet_targets = read_workbook_sheets(zip_file)

		for export in EXPORTS:
			sheet_name = export.sheet_name if export.sheet_name in sheet_targets else None
			if sheet_name is None:
				raise KeyError(f"Sheet '{export.sheet_name}' was not found in {input_file.name}.")

			rows = read_sheet_rows(zip_file, sheet_targets[sheet_name], shared_strings)
			csv_rows = sheet_to_csv_rows(rows, export.header_row)
			output_path = output_dir / export.output_name
			write_csv(output_path, csv_rows)
			print(f"Wrote {output_path}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
