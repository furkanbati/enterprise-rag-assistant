
from types import SimpleNamespace

from docling_core.types.doc import DocItemLabel

from document_parser import DocumentParser


class FakeDocument:
    def __init__(self, items):
        self.items = items

    def iterate_items(self):
        for item in self.items:
            yield item, None


class FakeConverter:
    def __init__(self, items):
        self.document = FakeDocument(items)
        self.received_path = None

    def convert(self, pdf_path):
        self.received_path = pdf_path
        return SimpleNamespace(document=self.document)


def make_item(
    label,
    text,
    level=1,
    page=1,
    with_provenance=True,
):
    provenance = (
        [SimpleNamespace(page_no=page)]
        if with_provenance
        else []
    )

    return SimpleNamespace(
        label=label,
        text=text,
        level=level,
        prov=provenance,
    )


def make_parser(items):
    parser = DocumentParser.__new__(DocumentParser)
    parser.converter = FakeConverter(items)
    return parser


def test_parse_groups_text_under_section_headings():
    parser = make_parser(
        [
            make_item(
                DocItemLabel.SECTION_HEADER,
                "Introduction",
                level=1,
                page=2,
            ),
            make_item(
                DocItemLabel.TEXT,
                "First paragraph.",
                page=2,
            ),
            make_item(
                DocItemLabel.SECTION_HEADER,
                "Methods",
                level=2,
                page=3,
            ),
            make_item(
                DocItemLabel.TEXT,
                "Method description.",
                page=3,
            ),
        ]
    )

    sections = parser.parse("guide.pdf")

    assert len(sections) == 2
    assert sections[0].heading == "Introduction"
    assert sections[0].level == 1
    assert sections[0].page == 2
    assert sections[0].text == "First paragraph."

    assert sections[1].heading == "Methods"
    assert sections[1].level == 2
    assert sections[1].page == 3
    assert sections[1].text == "Method description."
    assert parser.converter.received_path == "guide.pdf"


def test_parse_formats_list_items_as_bullets():
    parser = make_parser(
        [
            make_item(
                DocItemLabel.SECTION_HEADER,
                "Features",
            ),
            make_item(
                DocItemLabel.LIST_ITEM,
                "Search documents",
            ),
            make_item(
                DocItemLabel.LIST_ITEM,
                "Generate answers",
            ),
        ]
    )

    sections = parser.parse("guide.pdf")

    assert len(sections) == 1
    assert sections[0].text == (
        "- Search documents\n- Generate answers"
    )


def test_parse_uses_default_page_when_heading_has_no_provenance():
    parser = make_parser(
        [
            make_item(
                DocItemLabel.SECTION_HEADER,
                "Overview",
                with_provenance=False,
            ),
            make_item(
                DocItemLabel.TEXT,
                "Overview text.",
            ),
        ]
    )

    sections = parser.parse("guide.pdf")

    assert len(sections) == 1
    assert sections[0].page == 1


def test_parse_returns_empty_list_when_document_has_no_text():
    parser = make_parser(
        [
            make_item(
                DocItemLabel.SECTION_HEADER,
                "Empty section",
            ),
        ]
    )

    sections = parser.parse("empty.pdf")

    assert sections == []
