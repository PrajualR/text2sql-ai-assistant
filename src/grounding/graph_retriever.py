import json
import re
from pathlib import Path

from grounding.base import GroundingResult


class GraphRetriever:

    def __init__(self, knowledge_path: Path) -> None:
        self.knowledge_path = knowledge_path

        with self.knowledge_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.graph = json.load(file)

        self.kpis = self.graph["kpis"]
        self.dimensions = self.graph["dimensions"]
        self.business_synonyms = self.graph["business_synonyms"]

    def retrieve(self, question: str) -> GroundingResult:
        question = self._normalize(question)

        matched_terms = []
        resolved_kpis = {}
        resolved_dimensions = {}

        # --------------------------------------------------
        # 1. KPI-level aliases
        # --------------------------------------------------

        for kpi_key, kpi in self.kpis.items():

            terms = [
                kpi["name"],
                *kpi.get("aliases", []),
            ]

            matched_term = self._find_match(
                question,
                terms,
            )

            if matched_term:
                matched_terms.append(matched_term)

                resolved_kpis[kpi_key] = {
                    "key": kpi_key,
                    **kpi,
                }

        # --------------------------------------------------
        # 2. Business concepts
        # --------------------------------------------------

        for concept in self.business_synonyms.values():

            matched_term = self._find_match(
                question,
                concept["aliases"],
            )

            if not matched_term:
                continue

            matched_terms.append(matched_term)

            for kpi_key in concept["maps_to"]:

                kpi = self.kpis.get(kpi_key)

                if kpi:
                    resolved_kpis[kpi_key] = {
                        "key": kpi_key,
                        **kpi,
                    }

        # --------------------------------------------------
        # 3. Dimensions
        # --------------------------------------------------

        for dimension_key, dimension in self.dimensions.items():

            terms = [
                dimension_key,
                dimension["column"],
                *dimension.get("aliases", []),
            ]

            matched_term = self._find_match(
                question,
                terms,
            )

            if matched_term:

                matched_terms.append(matched_term)

                resolved_dimensions[dimension_key] = {
                    "key": dimension_key,
                    **dimension,
                }

        # --------------------------------------------------
        # 4. Build context
        # --------------------------------------------------

        kpis = list(resolved_kpis.values())
        dimensions = list(resolved_dimensions.values())

        context = self._build_context(
            kpis,
            dimensions,
        )

        columns = [kpi["column"] for kpi in kpis]

        columns.extend(dimension["column"] for dimension in dimensions)

        return GroundingResult(
            context=context,
            matched_terms=list(dict.fromkeys(matched_terms)),
            columns=list(dict.fromkeys(columns)),
        )

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()

        text = re.sub(
            r"[^a-z0-9%]+",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    @staticmethod
    def _find_match(
        question: str,
        terms: list[str],
    ) -> str | None:

        normalized_terms = [GraphRetriever._normalize(term) for term in terms if term]

        # Exact phrase matching only.
        for term in sorted(
            normalized_terms,
            key=len,
            reverse=True,
        ):

            if not term:
                continue

            if re.search(
                rf"(?<!\w){re.escape(term)}(?!\w)",
                question,
            ):
                return term

        return None

    @staticmethod
    def _build_context(
        kpis: list[dict],
        dimensions: list[dict],
    ) -> str:

        sections = []

        if kpis:
            sections.append("Relevant KPIs:")

            for kpi in kpis:

                template = kpi.get(
                    "context_template",
                    (
                        "{name} "
                        "(column: {column}, "
                        "aggregate with {aggregation}, "
                        "unit: {unit})"
                    ),
                )

                sections.append(
                    "- "
                    + template.format(
                        name=kpi["name"],
                        column=kpi["column"],
                        aggregation=kpi["aggregation"],
                        unit=kpi["unit"],
                    )
                )

        if dimensions:
            sections.append("\nRelevant dimensions:")

            for dimension in dimensions:

                sections.append(
                    "- " f"{dimension['key']} " f"(column: {dimension['column']})"
                )

        return "\n".join(sections)
