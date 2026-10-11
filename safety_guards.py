import re
from urllib.parse import urlsplit

from guardrails import Guard, settings
settings.rc.enable_metrics = False
settings.disable_tracing = True
from guardrails.validator_base import (
    Validator, register_validator, PassResult, FailResult,
)

# Exact hosts only; subdomains must be added explicitly.
ALLOWED_SEARCH_HOSTS = frozenset({
    "www.telekom.com",
    "www.vodafone.com",
})

PII_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"(?<!\w)\+?\d(?:[\s().-]*\d){8,14}(?!\w)"),
    re.compile(r"\b\d{4}-[A-Z]{5}\b", re.I),
)


@register_validator(name="local/no-customer-pii", data_type="string")
class NoCustomerPII(Validator):
    def _validate(self, value, metadata):
        text = str(value)
        if any(pattern.search(text) for pattern in PII_PATTERNS):
            return FailResult(error_message="Customer PII detected.")

        # Additional known identifiers supplied by the application.
        for item in metadata.get("sensitive_values", []):
            if item and str(item).casefold() in text.casefold():
                return FailResult(error_message="Customer identifier detected.")

        return PassResult()


PII_GUARD = Guard().use(NoCustomerPII(on_fail="exception"))


def validate_public_output(text: str, sensitive_values=()) -> str:
    outcome = PII_GUARD.validate(
        text,
        metadata={"sensitive_values": list(sensitive_values)},
    )
    if not outcome.validation_passed:
        raise ValueError("Output failed PII validation.")
    return outcome.validated_output


def validate_search_url(url: str) -> str:
    if not isinstance(url, str) or any(c.isspace() for c in url):
        raise ValueError("Invalid search URL.")

    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid search URL.") from None

    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_SEARCH_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        raise ValueError("Search URL outside domain allowlist.")

    return url


if __name__ == "__main__":
    assert validate_public_output(
        "We can offer a 10% loyalty discount."
    )
    print("PASS: safe output")

    for text, identifiers in [
        ("Email: customer@example.com", ()),
        ("Phone: +48 123 456 789", ()),
        ("Customer: 1234-ABCDE", ()),
        ("Account: private-account-42", ("private-account-42",)),
    ]:
        try:
            validate_public_output(text, identifiers)
        except Exception:
            print("PASS: PII blocked")
        else:
            raise AssertionError("PII was not blocked.")

    assert validate_search_url("https://www.telekom.com/en")
    print("PASS: allowed domain")

    for url in [
        "https://evil.example",
        "https://www.telekom.com.evil.example",
        "https://www.telekom.com@evil.example",
        "http://www.telekom.com",
        "https://www.telekom.com:8443",
    ]:
        try:
            validate_search_url(url)
        except ValueError:
            print("PASS: unauthorized URL blocked")
        else:
            raise AssertionError("Unauthorized URL accepted.")

    print("SAFETY CHECK PASSED")
