from dataclasses import dataclass


@dataclass(frozen=True)
class InfojobsSelectors:
    search_url: str = "https://www.infojobs.com.br/empregos.aspx?Palabra={query}"
    listing_item: str = "a[href*='/vaga-de-'], a[href*='/empregos/']"
    job_title: str = "h1, .vacancy-title, [class*='title']"
    job_company: str = "[class*='company'], [class*='empresa'] a"
    job_location: str = "[class*='location'], [class*='localidade']"
    job_description_section: str = (
        "[class*='vacancy-description'], [class*='description-box'], section[id*='description']"
    )


SELECTORS = InfojobsSelectors()
