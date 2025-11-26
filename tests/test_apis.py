"""
Teste pentru API-uri
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, date

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import (
    validate_iata_code,
    validate_date,
    validate_passengers,
    validate_search_params
)
from utils.helpers import (
    format_duration,
    format_price,
    get_stops_description
)


class TestValidators(unittest.TestCase):
    """Teste pentru validatori"""
    
    def test_validate_iata_code_valid(self):
        """Test cod IATA valid"""
        is_valid, error = validate_iata_code("OTP")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_validate_iata_code_lowercase(self):
        """Test cod IATA lowercase"""
        is_valid, error = validate_iata_code("otp")
        self.assertTrue(is_valid)
    
    def test_validate_iata_code_invalid_length(self):
        """Test cod IATA lungime invalidă"""
        is_valid, error = validate_iata_code("OTPP")
        self.assertFalse(is_valid)
        self.assertIn("3 characters", error)
    
    def test_validate_iata_code_numbers(self):
        """Test cod IATA cu numere"""
        is_valid, error = validate_iata_code("OT1")
        self.assertFalse(is_valid)
        self.assertIn("only letters", error)
    
    def test_validate_iata_code_empty(self):
        """Test cod IATA gol"""
        is_valid, error = validate_iata_code("")
        self.assertFalse(is_valid)
    
    def test_validate_date_valid(self):
        """Test dată validă"""
        future_date = "2025-12-25"
        is_valid, error, parsed = validate_date(future_date)
        self.assertTrue(is_valid)
        self.assertIsNotNone(parsed)
    
    def test_validate_date_past(self):
        """Test dată în trecut"""
        past_date = "2020-01-01"
        is_valid, error, parsed = validate_date(past_date, min_date=date.today())
        self.assertFalse(is_valid)
    
    def test_validate_passengers_valid(self):
        """Test pasageri valid"""
        is_valid, error = validate_passengers(2, 1, 1)
        self.assertTrue(is_valid)
    
    def test_validate_passengers_no_adults(self):
        """Test fără adulți"""
        is_valid, error = validate_passengers(0, 1, 0)
        self.assertFalse(is_valid)
    
    def test_validate_passengers_too_many_infants(self):
        """Test prea mulți bebeluși"""
        is_valid, error = validate_passengers(1, 0, 2)
        self.assertFalse(is_valid)
    
    def test_validate_passengers_too_many_total(self):
        """Test prea mulți pasageri total"""
        is_valid, error = validate_passengers(5, 3, 2)
        self.assertFalse(is_valid)


class TestHelpers(unittest.TestCase):
    """Teste pentru funcții helper"""
    
    def test_format_duration_iso(self):
        """Test formatare durată ISO"""
        result = format_duration("PT2H30M")
        self.assertEqual(result, "2h 30m")
    
    def test_format_duration_hours_only(self):
        """Test formatare durată doar ore"""
        result = format_duration("PT3H")
        self.assertEqual(result, "3h")
    
    def test_format_duration_minutes_only(self):
        """Test formatare durată doar minute"""
        result = format_duration("PT45M")
        self.assertEqual(result, "45m")
    
    def test_format_price_eur(self):
        """Test formatare preț EUR"""
        result = format_price(123.45, "EUR")
        self.assertEqual(result, "€123.45")
    
    def test_format_price_usd(self):
        """Test formatare preț USD"""
        result = format_price(99.99, "USD")
        self.assertEqual(result, "$99.99")
    
    def test_format_price_ron(self):
        """Test formatare preț RON"""
        result = format_price(500.00, "RON")
        self.assertEqual(result, "500.00 lei")
    
    def test_get_stops_description_direct(self):
        """Test descriere direct"""
        result = get_stops_description(0)
        self.assertEqual(result, "Direct")
    
    def test_get_stops_description_one(self):
        """Test descriere o escală"""
        result = get_stops_description(1)
        self.assertEqual(result, "1 stop")
    
    def test_get_stops_description_multiple(self):
        """Test descriere mai multe escale"""
        result = get_stops_description(2)
        self.assertEqual(result, "2 stops")


class TestSearchValidation(unittest.TestCase):
    """Teste pentru validarea căutării complete"""
    
    def test_valid_search(self):
        """Test căutare validă"""
        is_valid, errors = validate_search_params(
            origin="OTP",
            destination="FCO",
            departure_date="2025-08-15",
            adults=2
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_same_origin_destination(self):
        """Test origine și destinație identice"""
        is_valid, errors = validate_search_params(
            origin="OTP",
            destination="OTP",
            departure_date="2025-08-15",
            adults=1
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("different" in e.lower() for e in errors))
    
    def test_return_before_departure(self):
        """Test întoarcere înainte de plecare"""
        is_valid, errors = validate_search_params(
            origin="OTP",
            destination="FCO",
            departure_date="2025-08-15",
            return_date="2025-08-10",
            adults=1
        )
        self.assertFalse(is_valid)


if __name__ == '__main__':
    unittest.main()
