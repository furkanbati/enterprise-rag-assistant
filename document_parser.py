from pathlib import Path

from docling_core.types.doc import DocItemLabel
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from models import Section

# Docling parses everything except plain text, which is read directly.
SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".html", ".htm", ".md", ".txt")


class DocumentParser:
    def __init__(self) -> None:
        options = PdfPipelineOptions()
        # We only need document structure for heading-aware chunking.
        # Disable expensive features to improve ingestion performance.
        options.do_ocr = False
        options.do_table_structure = False
        options.generate_parsed_pages = False

        options.do_picture_description = False
        options.do_code_enrichment = False
        
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.MD,
            ],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=options,
                )
            }
        )
    
    def parse(self, path: str) -> list[Section]:
        """Parse a document into sections.

        Formats without pages (DOCX, HTML, Markdown, text) put every section
        on page 1.
        """

        if Path(path).suffix.lower() == ".txt":
            return self._parse_text(path)

        result = self.converter.convert(path)
        document = result.document

        sections: list[Section] = []

        current_heading = ""
        current_level = 0
        current_page = 1
        current_text: list[str] = []

        for item, _ in document.iterate_items():

            match item.label:

                # DOCX, HTML and Markdown mark the document heading as a title.
                case DocItemLabel.TITLE | DocItemLabel.SECTION_HEADER:
                    self._flush_section(
                        sections,
                        current_heading,
                        current_level,
                        current_page,
                        current_text,
                    )

                    current_heading = item.text.strip()
                    current_level = getattr(item, "level", None) or 1
                    current_page = self._get_page(item)
                    current_text = []

                # DOCX paragraphs are labelled as paragraphs, not text.
                case DocItemLabel.TEXT | DocItemLabel.PARAGRAPH:
                    current_text.append(item.text)

                case DocItemLabel.LIST_ITEM:
                    current_text.append(f"- {item.text}")

        self._flush_section(
            sections,
            current_heading,
            current_level,
            current_page,
            current_text,
        )

        return sections

    @staticmethod
    def _parse_text(path: str) -> list[Section]:
        text = Path(path).read_text(encoding="utf-8", errors="replace").strip()

        if not text:
            return []

        return [Section(heading="", level=1, page=1, text=text)]

    @staticmethod
    def _flush_section(
        sections: list[Section],
        heading: str,
        level: int,
        page: int,
        text: list[str],
    ) -> None:
        if not text:
            return

        sections.append(
            Section(
                heading=heading,
                level=level,
                page=page,
                text="\n".join(text).strip(),
            )
        )

    @staticmethod
    def _get_page(item) -> int:
        if not getattr(item, "prov", None):
            return 1

        return item.prov[0].page_no