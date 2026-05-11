from dataclasses import dataclass


@dataclass(frozen=True)
class GupySelectors:
    search_url: str = "https://portal.gupy.io/job-search/term={query}"
    listing_item: str = "a[href*='gupy.io/job/'], a[href*='/jobs/']"
    job_title: str = "h1"
    job_description_section: str = "[data-testid='text-section']"


SELECTORS = GupySelectors()
