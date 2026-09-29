from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    out = scrub_text("CCCD: 079123456789")
    assert "079123456789" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card_formats() -> None:
    card_numbers = (
        "4111111111111111",
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
    )

    for card_number in card_numbers:
        out = scrub_text(f"Card: {card_number}")
        assert card_number not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_scrub_email_plus_alias_and_nested_exception() -> None:
    from app.logging_config import scrub_event
    raw = "learner+lab@example.com"
    result = scrub_event(None, "error", {"exception": raw, "payload": {"nested": [raw]}})
    assert raw not in str(result)
    assert result["payload"]["nested"] == ["[REDACTED_EMAIL]"]


def test_card_with_phone_like_prefix_is_fully_redacted() -> None:
    assert scrub_text("0901 2345 6789 1234") == "[REDACTED_CREDIT_CARD]"
