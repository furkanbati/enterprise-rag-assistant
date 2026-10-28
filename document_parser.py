import logging
from functools import partial
from pathlib import Path

from docling_core.types.doc import DocItemLabel
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    OcrOptions,
    PdfPipelineOptions,
    RapidOcrOptions,
)
from models import Section

logger = logging.getLogger(__name__)

# Docling parses everything except plain text, which is read directly.
SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".html", ".htm", ".md", ".txt")

# On two scanned pages RapidOCR took about 9 s per page and EasyOCR about 27 s.
OCR_ENGINES = {
    "rapidocr": RapidOcrOptions,
    "easyocr": partial(EasyOcrOptions, lang=["en"]),
}
OCR_DISABLED = "off"


class DocumentParser:
    def __init__(self, ocr_engine: str = "rapidocr") -> None:
        self.converter = self._build_converter(ocr_options=None)
        # Scanned PDFs have no text layer. OCR is slow, so it only runs
        # when the regular pass finds no text.
        self.ocr_converter = (
            None
            if ocr_engine == OCR_DISABLED
            else self._build_converter(ocr_options=self._ocr_options(ocr_engine))
        )

    @staticmethod
    def _ocr_options(engine: str) -> OcrOptions:
        if engine not in OCR_ENGINES:
            choices = " or ".join(f"'{name}'" for name in [*OCR_ENGINES, OCR_DISABLED])
            raise ValueError(f"Unknown OCR engine '{engine}'. Use {choices}.")

        return OCR_ENGINES[engine](force_full_page_ocr=True)

    @staticmethod
    def _build_converter(ocr_options: OcrOptions | None) -> DocumentConverter:
        options = PdfPipelineOptions()
        # We only need document structure for heading-aware chunking.
        # Disable expensive features to improve ingestion performance.
        options.do_ocr = ocr_options is not None
        if ocr_options is not None:
            options.ocr_options = ocr_options
        options.do_table_structure = False
        options.generate_parsed_pages = False

        options.do_picture_description = False
        options.do_code_enrichment = False

        return DocumentConverter(
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

        suffix = Path(path).suffix.lower()

        if suffix == ".txt":
            return self._parse_text(path)

        sections = self._parse_document(self.converter, path)

        if not sections and suffix == ".pdf" and self.ocr_converter:
            logger.info("No text layer in %s, retrying with OCR", Path(path).name)
            sections = self._parse_document(self.ocr_converter, path)

        return sections

    def _parse_document(self, converter: DocumentConverter, path: str) -> list[Section]:
        result = converter.convert(path)
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