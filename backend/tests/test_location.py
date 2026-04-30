"""
Unit tests for location normalizer and gate functions.
Run with: docker compose exec backend pytest tests/test_location.py -v
"""
import pytest
from app.location import extract_city, is_preferred, is_acceptable, is_excluded


# ─── extract_city tests ───────────────────────────────────────────────────────

class TestExtractCity:

    # ── Clean location field ──────────────────────────────────────────────────

    def test_vancouver_in_field(self):
        assert extract_city("Vancouver, BC", "") == "Unknown"

    def test_calgary_in_field(self):
        assert extract_city("Calgary, Calgary region", "") == "Unknown"

    def test_ottawa_in_field(self):
        assert extract_city("Ottawa, Ontario", "") == "Ottawa"

    def test_montreal_in_field(self):
        assert extract_city("Montréal, Québec", "") == "Montreal"

    def test_montreal_no_accent(self):
        assert extract_city("Montreal, Quebec", "") == "Montreal"

    def test_remote_in_field(self):
        assert extract_city("Remote", "") == "Remote"

    def test_remote_lowercase(self):
        assert extract_city("remote", "") == "Remote"

    def test_work_from_home_in_field(self):
        assert extract_city("Work from home", "") == "Remote"

    # ── Gatineau / Ottawa equivalences ───────────────────────────────────────

    def test_gatineau_maps_to_ottawa(self):
        assert extract_city("Gatineau, Quebec", "") == "Ottawa"

    def test_kanata_maps_to_ottawa(self):
        assert extract_city("Kanata, Ontario", "") == "Ottawa"

    def test_nepean_maps_to_ottawa(self):
        assert extract_city("Nepean, Ontario", "") == "Ottawa"

    def test_hull_maps_to_ottawa(self):
        assert extract_city("Hull, Quebec", "") == "Ottawa"

    def test_orleans_maps_to_ottawa(self):
        assert extract_city("Orléans, Ontario", "") == "Ottawa"

    # ── Montreal equivalences ─────────────────────────────────────────────────

    def test_laval_maps_to_montreal(self):
        assert extract_city("Laval, Quebec", "") == "Montreal"

    def test_longueuil_maps_to_montreal(self):
        assert extract_city("Longueuil, Quebec", "") == "Montreal"

    # ── Vague field — scan description ───────────────────────────────────────

    def test_canada_field_vancouver_in_desc(self):
        desc = "This position is based in Vancouver, BC, Canada - Hybrid"
        assert extract_city("Canada", desc) == "Unknown"

    def test_canada_field_ottawa_in_desc(self):
        desc = "Our Ottawa, Ontario office is looking for a senior engineer"
        assert extract_city("Canada", desc) == "Ottawa"

    def test_canada_field_gatineau_in_desc(self):
        desc = "Position located in Gatineau, QC with hybrid schedule"
        assert extract_city("Canada", desc) == "Ottawa"

    def test_canada_field_montreal_in_desc(self):
        desc = "Join our Montréal team in the heart of downtown"
        assert extract_city("Canada", desc) == "Montreal"

    def test_canada_field_remote_in_desc(self):
        desc = "This is a fully remote position open to all Canadian residents"
        assert extract_city("Canada", desc) == "Remote"

    def test_canada_field_wfh_in_desc(self):
        desc = "Work from home opportunity, flexible hours"
        assert extract_city("Canada", desc) == "Remote"

    def test_canada_field_no_city_in_desc(self):
        desc = "Competitive salary, great benefits, dynamic team environment"
        assert extract_city("Canada", desc) == "Unknown"

    # ── Hybrid handling ───────────────────────────────────────────────────────

    def test_hybrid_ottawa_in_field(self):
        assert extract_city("Ottawa - Hybrid", "") == "Ottawa"

    def test_hybrid_no_city_in_field_ottawa_in_desc(self):
        desc = "Hybrid role based out of our Ottawa office"
        assert extract_city("Hybrid", desc) == "Ottawa"

    def test_hybrid_no_city_anywhere(self):
        # Hybrid with no city → Remote
        assert extract_city("Hybrid", "Competitive benefits package") == "Remote"

    def test_hybrid_vancouver_excluded(self):
        desc = "Hybrid position in Vancouver, BC"
        assert extract_city("Canada", desc) == "Unknown"

    def test_hybrid_montreal_field(self):
        assert extract_city("Montréal - Hybrid", "") == "Montreal"

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_empty_fields(self):
        assert extract_city("", "") == "Unknown"

    def test_only_spaces(self):
        assert extract_city("   ", "   ") == "Unknown"

    def test_desc_only_first_600_chars_scanned(self):
        # City appears after 600 chars — should not be found
        prefix = "a " * 300  # ~600 chars
        desc = prefix + "Ottawa, Ontario office"
        assert extract_city("Canada", desc) == "Unknown"

    def test_desc_city_within_600_chars(self):
        prefix = "a " * 200  # ~400 chars
        desc = prefix + "Ottawa, Ontario office"
        assert extract_city("Canada", desc) == "Ottawa"


# ─── is_preferred tests ───────────────────────────────────────────────────────

class TestIsPreferred:

    def test_ottawa_preferred(self):
        assert is_preferred("Ottawa") is True

    def test_remote_preferred(self):
        assert is_preferred("Remote") is True

    def test_montreal_not_preferred(self):
        assert is_preferred("Montreal") is False

    def test_unknown_not_preferred(self):
        assert is_preferred("Unknown") is False

    def test_vancouver_not_preferred(self):
        assert is_preferred("Vancouver") is False


# ─── is_acceptable tests ─────────────────────────────────────────────────────

class TestIsAcceptable:

    def test_montreal_acceptable(self):
        assert is_acceptable("Montreal") is True

    def test_ottawa_not_acceptable(self):
        assert is_acceptable("Ottawa") is False

    def test_remote_not_acceptable(self):
        assert is_acceptable("Remote") is False

    def test_unknown_not_acceptable(self):
        assert is_acceptable("Unknown") is False


# ─── is_excluded tests ────────────────────────────────────────────────────────

class TestIsExcluded:

    def test_vancouver_excluded(self):
        assert is_excluded(extract_city("Vancouver, BC", "")) is True

    def test_calgary_excluded(self):
        assert is_excluded(extract_city("Calgary, Calgary region", "")) is True

    def test_toronto_excluded(self):
        assert is_excluded(extract_city("Toronto, Ontario", "")) is True

    def test_edmonton_excluded(self):
        assert is_excluded(extract_city("Edmonton, Alberta", "")) is True

    def test_unknown_excluded(self):
        assert is_excluded("Unknown") is True

    def test_ottawa_not_excluded(self):
        assert is_excluded("Ottawa") is False

    def test_remote_not_excluded(self):
        assert is_excluded("Remote") is False

    def test_montreal_not_excluded(self):
        assert is_excluded("Montreal") is False


# ─── Full pipeline gate integration ──────────────────────────────────────────

class TestPipelineGate:
    """
    Simulate the pipeline run loop decision for a set of representative jobs.
    Each job has a location_field and description snippet.
    We verify the gate decision (score vs drop) without calling Groq.
    """

    JOBS = [
        # (description, location_field, description, expected_pass)
        ("Ottawa role",         "Ottawa, Ontario",      "",                                         True),
        ("Gatineau role",       "Gatineau, Quebec",     "",                                         True),
        ("Remote role",         "Remote",               "",                                         True),
        ("WFH role",            "Canada",               "This is a work from home opportunity",     True),
        ("Montreal role",       "Montréal, Québec",     "",                                         True),
        ("Laval role",          "Laval, Quebec",        "",                                         True),
        ("Vancouver role",      "Vancouver, BC",        "",                                         False),
        ("Calgary role",        "Calgary region",       "",                                         False),
        ("Toronto role",        "Toronto, Ontario",     "",                                         False),
        ("Van in desc",         "Canada",               "Vancouver, BC, Canada - Hybrid",           False),
        ("Ottawa in desc",      "Canada",               "Position in Ottawa, Ontario",              True),
        ("Unknown",             "Canada",               "Great benefits, competitive salary",       False),
        ("Ottawa hybrid",       "Ottawa - Hybrid",      "",                                         True),
        ("Hybrid no city",      "Hybrid",               "No city mentioned here",                   True),  # → Remote
        ("MTL hybrid",          "Montréal - Hybrid",    "",                                         True),
    ]

    @pytest.mark.parametrize("label,loc_field,desc,expected_pass", JOBS)
    def test_gate(self, label, loc_field, desc, expected_pass):
        city = extract_city(loc_field, desc)
        passes = not is_excluded(city)
        assert passes == expected_pass, (
            f"[{label}] extract_city('{loc_field}', ...) → '{city}' "
            f"→ excluded={is_excluded(city)}, expected_pass={expected_pass}"
        )
