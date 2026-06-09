# import re


# class MetadataOps:
#     """
#     Extracts news article metadata using rule-based patterns.
#     """

#     NEWS_AGENCIES = [
#         "PTI",
#         "ANI",
#         "Reuters",
#         "AP",
#         "AFP",
#         "IANS",
#         "UNI",
#         "Bloomberg",
#     ]

#     PUBLISHERS = [
#         "The Hindu",
#         "The Indian Express",
#         "Times of India",
#         "Hindustan Times",
#         "BBC",
#         "CNN",
#         "NDTV",
#         "Al Jazeera",
#         "The Wire",
#         "Scroll",
#     ]

#     def init(self):
#         pass

#     def extract(self, text: str) -> dict:
#         return {
#             "author": self.extract_author(text),
#             "reporter": self.extract_reporter(text),
#             "news_agency": self.extract_news_agency(text),
#             "publisher": self.extract_publisher(text),
#             "location": self.extract_location(text),
#             "publication_date": self.extract_date(text),
#         }

#     def extract_author(self, text: str):
#         patterns = [
#             r"By\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
#             r"Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
#             r"Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
#         ]

#         for pattern in patterns:
#             match = re.search(pattern, text)
#             if match:
#                 return match.group(1).strip()

#         return None

#     def extract_reporter(self, text: str):
#         patterns = [
#             r"Reported by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
#             r"Special Correspondent\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
#             r"Staff Reporter\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
#         ]

#         for pattern in patterns:
#             match = re.search(pattern, text)
#             if match:
#                 return match.group(1).strip()

#         return None

#     def extract_news_agency(self, text: str):
#         for agency in self.NEWS_AGENCIES:
#             if re.search(rf"\b{re.escape(agency)}\b", text, re.IGNORECASE):
#                 return agency

#         return None

#     def extract_publisher(self, text: str):
#         for publisher in self.PUBLISHERS:
#             if publisher.lower() in text.lower():
#                 return publisher

#         match = re.search(
#             r"Published by\s+([A-Z][A-Za-z\s&]+)",
#             text
#         )

#         if match:
#             return match.group(1).strip()

#         return None

#     def extract_location(self, text: str):
#         patterns = [
#             r"^([A-Z][A-Za-z\s]+):",
#             r"^([A-Z][A-Za-z\s]+),\s*[A-Z][a-z]+\s+\d{1,2}:",
#             r"^([A-Z][A-Za-z\s]+),",
#         ]

#         first_lines = "\n".join(text.split("\n")[:5])

#         for pattern in patterns:
#             match = re.search(pattern, first_lines, re.MULTILINE)
#             if match:
#                 return match.group(1).strip()

#         return None

#     def extract_date(self, text: str):
#         patterns = [
#             r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
#             r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
#         ]

#         for pattern in patterns:
#             match = re.search(pattern, text)
#             if match:
#                 return match.group(0)

#         return None

import re


class MetadataOps:
    """
    Extracts news article metadata using spaCy + rule-based patterns.
    """

    NEWS_AGENCIES = [
        "PTI",
        "ANI",
        "Reuters",
        "AP",
        "AFP",
        "IANS",
        "UNI",
        "Bloomberg",
    ]

    PUBLISHERS = [
        "The Hindu",
        "The Indian Express",
        "Times of India",
        "Hindustan Times",
        "BBC",
        "CNN",
        "NDTV",
        "Al Jazeera",
        "The Wire",
        "Scroll",
    ]

    def __init__(self, nlp):
        self.nlp = nlp

    def extract(self, text: str) -> dict:

        author, location = self._extract_author_location_from_header(text)

        return {
            "author": author,
            "reporter": self.extract_reporter(text),
            "news_agency": self.extract_news_agency(text),
            "publisher": self.extract_publisher(text),
            "location": location,
            "publication_date": self.extract_date(text),
        }

    # def _extract_author_location_from_header(self, text: str):

    #     # Metadata is usually near the top
    #     header = text[:500]

    #     doc = self.nlp(header)

    #     author = None
    #     location = None

    #     for ent in doc.ents:

    #         if author is None and ent.label_ == "PERSON":
    #             author = ent.text.strip()

    #         elif location is None and ent.label_ in ("GPE", "LOC"):
    #             location = ent.text.strip()

    #         if author and location:
    #             break

    #     return author, location

    def _extract_author_location_from_header(self, text: str):

        lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        ][:5]

        author = None
        location = None

    # By Rit Nanda
        if lines:

            first_line = lines[0]

            if first_line.lower().startswith("by "):
                author = first_line[3:].strip()

    # New Delhi usually next line
        if len(lines) > 1:

            candidate = lines[1]

            doc = self.nlp(candidate)

            for ent in doc.ents:

                if ent.label_ in ("GPE", "LOC"):
                    location = ent.text.strip()
                    break

        return author, location

    def extract_author(self, text: str):

        author, _ = self._extract_author_location_from_header(text)

        return author

    def extract_location(self, text: str):

        _, location = self._extract_author_location_from_header(text)

        return location

    def extract_reporter(self, text: str):

        patterns = [
            r"Reported by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"Special Correspondent\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"Staff Reporter\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]

        for pattern in patterns:

            match = re.search(pattern, text)

            if match:
                return match.group(1).strip()

        return None

    def extract_news_agency(self, text: str):

        for agency in self.NEWS_AGENCIES:

            if re.search(
                rf"\b{re.escape(agency)}\b",
                text,
                re.IGNORECASE
            ):
                return agency

        return None

    def extract_publisher(self, text: str):

        for publisher in self.PUBLISHERS:

            if publisher.lower() in text.lower():
                return publisher

        match = re.search(
            r"Published by\s+([A-Z][A-Za-z\s&]+)",
            text
        )

        if match:
            return match.group(1).strip()

        return None

    def extract_date(self, text: str):

        patterns = [
            r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
        ]

        for pattern in patterns:

            match = re.search(pattern, text)

            if match:
                return match.group(0)

        return None