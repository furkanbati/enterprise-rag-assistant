from ingestion import Ingestion
from metadata import HeadingDetector

pages = Ingestion._extract_text("NIST.AI.100-1.pdf")

detector = HeadingDetector()

sections = detector.extract_sections(pages)

for section in sections:
    print("=" * 80)
    print("Heading:", section.heading.text if section.heading else None)
    print("Level:", section.heading.level if section.heading else None)
    print("Page:", section.page)
    print(section.text[:300])
    print()