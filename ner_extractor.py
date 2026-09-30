import re
import spacy


class NERExtractor:
    """Resume NER with header-first candidate-name detection."""

    def __init__(self, model_name="en_core_web_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError as exc:
            raise RuntimeError(
                "spaCy model not found. Run: python -m spacy download en_core_web_sm"
            ) from exc

    @staticmethod
    def _clean_line(line):
        return re.sub(r"\s+", " ", line).strip(" |•\t\r\n")

    @staticmethod
    def _is_heading(line):
        headings = {
            "resume", "cv", "curriculum vitae", "professional summary", "summary",
            "profile", "objective", "education", "experience", "work experience",
            "employment", "technical skills", "skills", "projects", "academic projects",
            "personal projects", "certifications", "certification", "achievements",
            "contact", "contact information", "references", "interests", "hobbies"
        }
        return line.lower().strip().rstrip(":") in headings

    @staticmethod
    def _is_contact_line(line):
        low = line.lower()
        return (
            "@" in line or "linkedin.com" in low or "github.com" in low
            or "portfolio" in low or bool(re.search(r"\+?\d[\d\s().-]{8,}\d", line))
        )

    def _find_header_name(self, text):
        lines = [self._clean_line(x) for x in text.splitlines()]
        lines = [x for x in lines if x]

        header = []
        for line in lines[:25]:
            if self._is_heading(line):
                break
            header.append(line)

        candidates = [
            x for x in header
            if not self._is_contact_line(x) and not self._is_heading(x)
        ]

        blocked = {
            "resume", "curriculum", "vitae", "developer", "engineer", "student",
            "profile", "summary", "generative", "artificial", "intelligence",
            "machine", "learning", "software", "computer", "science"
        }

        # 1. Strongest signal: standalone uppercase human-name-like line.
        for line in candidates:
            words = re.findall(r"[A-Za-z][A-Za-z.'-]*", line)
            if 2 <= len(words) <= 5 and line == line.upper():
                if not any(w.lower() in blocked for w in words):
                    return line.title()

        # 2. Title-case short line in the header.
        for line in candidates:
            words = re.findall(r"[A-Za-z][A-Za-z.'-]*", line)
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                if not any(w.lower() in blocked for w in words):
                    return line

        # 3. spaCy PERSON only as a fallback, restricted to the header.
        doc = self.nlp("\n".join(header[:15]))
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                candidate = self._clean_line(ent.text)
                words = candidate.split()
                if 2 <= len(words) <= 4 and not any(w.lower() in blocked for w in words):
                    return candidate

        return None

    def extract(self, text):
        doc = self.nlp(text)
        entities = []
        organizations = []

        for ent in doc.ents:
            value = ent.text.strip()
            if not value:
                continue
            entities.append({"text": value, "label": ent.label_})
            if ent.label_ in {"ORG", "GPE", "FAC"}:
                organizations.append(value)

        return {
            "name": self._find_header_name(text),
            "entities": entities,
            "organizations": list(dict.fromkeys(organizations)),
        }
