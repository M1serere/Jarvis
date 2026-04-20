from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from tools.base import BaseTool

DESKTOP_DIR = Path.home() / "Desktop"

FILE_TYPE_ALIASES = {
    "text": "txt",
    "txt": "txt",
    "текст": "txt",
    "текстовый": "txt",
    "word": "docx",
    "doc": "docx",
    "docx": "docx",
    "ворд": "docx",
    "wordfile": "docx",
    "excel": "xlsx",
    "xls": "xlsx",
    "xlsx": "xlsx",
    "эксель": "xlsx",
    "таблица": "xlsx",
    "powerpoint": "pptx",
    "power point": "pptx",
    "ppt": "pptx",
    "pptx": "pptx",
    "поверпоинт": "pptx",
    "пауэрпоинт": "pptx",
    "презентация": "pptx",
}

SUPPORTED_EXTENSIONS = {"docx", "pptx", "xlsx"}


class CreateFileTool(BaseTool):
    name = "create_file"
    description = (
        "Создаёт файл на рабочем столе по умолчанию. "
        "Поддерживает текстовые файлы, а также Word (.docx), Excel (.xlsx) "
        "и PowerPoint (.pptx). Можно передавать filename, content и file_type."
    )
    risk_level = "confirm"

    def run(self, args: dict[str, Any]) -> str:
        filename = str(args.get("filename", "")).strip()
        content = str(args.get("content", ""))
        requested_type = _normalize_file_type(
            args.get("file_type") or args.get("program") or args.get("app")
        )

        if not filename:
            return "Не удалось создать файл: имя файла не указано."

        target_dir = DESKTOP_DIR if DESKTOP_DIR.exists() else Path.home()
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = Path(filename).name
        final_filename = _apply_extension_if_needed(safe_filename, requested_type)
        file_path = target_dir / final_filename
        effective_type = requested_type or _infer_file_type(file_path)

        if file_path.exists():
            return f"Файл уже существует: {final_filename}"

        try:
            if effective_type == "docx":
                _write_docx(file_path, content)
            elif effective_type == "xlsx":
                _write_xlsx(file_path, content)
            elif effective_type == "pptx":
                _write_pptx(file_path, content)
            else:
                file_path.write_text(content, encoding="utf-8")
        except Exception as exc:
            return f"Не удалось создать файл {final_filename}: {exc}"

        if content.strip():
            return f"Файл создан: {final_filename}. Путь: {file_path}"
        return f"Файл создан: {final_filename}. Путь: {file_path}"


def _normalize_file_type(raw_value: Any) -> str | None:
    if raw_value is None:
        return None

    normalized = str(raw_value).strip().lower()
    if not normalized:
        return None

    return FILE_TYPE_ALIASES.get(normalized, normalized.lstrip("."))


def _apply_extension_if_needed(filename: str, file_type: str | None) -> str:
    path = Path(filename)
    if path.suffix or not file_type:
        return filename
    return f"{filename}.{file_type}"


def _infer_file_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower().lstrip(".")
    if suffix in SUPPORTED_EXTENSIONS:
        return suffix
    return "txt"


def _build_word_paragraphs(content: str) -> str:
    if not content:
        return "<w:p/>"

    paragraphs: list[str] = []
    for line in content.splitlines():
        if not line:
            paragraphs.append("<w:p/>")
            continue
        paragraphs.append(
            "<w:p><w:r><w:t xml:space=\"preserve\">"
            f"{escape(line)}"
            "</w:t></w:r></w:p>"
        )
    return "".join(paragraphs)


def _write_docx(file_path: Path, content: str) -> None:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:v="urn:schemas-microsoft-com:vml"
 xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:w10="urn:schemas-microsoft-com:office:word"
 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
 xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 wp14">
  <w:body>
    {_build_word_paragraphs(content)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

    with ZipFile(file_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("word/document.xml", document_xml)


def _build_sheet_rows(content: str) -> str:
    if not content:
        return ""

    rows: list[str] = []
    for index, line in enumerate(content.splitlines(), start=1):
        cell_ref = f"A{index}"
        rows.append(
            f"<row r=\"{index}\">"
            f"<c r=\"{cell_ref}\" t=\"inlineStr\"><is><t>{escape(line)}</t></is></c>"
            "</row>"
        )
    return "".join(rows)


def _write_xlsx(file_path: Path, content: str) -> None:
    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""

    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{_build_sheet_rows(content)}</sheetData>
</worksheet>
"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""

    root_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""

    workbook_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""

    with ZipFile(file_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def _write_pptx(file_path: Path, content: str) -> None:
    try:
        import pythoncom
        from win32com.client import DispatchEx
    except ImportError as exc:
        raise RuntimeError("PowerPoint automation недоступна") from exc

    title_text = ""
    body_text = ""
    if content.strip():
        lines = content.splitlines()
        title_text = lines[0]
        body_text = "\n".join(lines[1:]).strip()

    app = None
    presentation = None
    pythoncom.CoInitialize()
    try:
        app = DispatchEx("PowerPoint.Application")
        app.Visible = 1
        presentation = app.Presentations.Add()
        slide = presentation.Slides.Add(1, 2)

        if title_text:
            try:
                slide.Shapes.Title.TextFrame.TextRange.Text = title_text
            except Exception:
                pass

        if body_text:
            try:
                slide.Shapes.Placeholders(2).TextFrame.TextRange.Text = body_text
            except Exception:
                pass

        presentation.SaveAs(str(file_path))
    except Exception as exc:
        raise RuntimeError(
            "Не удалось создать файл PowerPoint. Проверь, установлен ли Microsoft PowerPoint."
        ) from exc
    finally:
        if presentation is not None:
            try:
                presentation.Close()
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()
