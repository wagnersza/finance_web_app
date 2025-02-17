import unittest
from app.routes import convert_brazilian_amount_to_float

class TestAmountFormatting(unittest.TestCase):
    def test_brazilian_amount_conversion(self):
        test_cases = [
            ("3.333,99", 3333.99),
            ("1.000.000,22", 1000000.22),
            ("3.000,44", 3000.44),
            ("444,99", 444.99),
            ("1.234.567,89", 1234567.89),
            ("0,50", 0.50),
            ("1.000,00", 1000.00),
            ("10.000,00", 10000.00),
            ("1000", 1000.0),  # Test whole number without decimals
            ("1.000", 1000.0),  # Test whole number with thousand separator
            ("1.000.000", 1000000.0),  # Test large whole number
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = convert_brazilian_amount_to_float(input_str)
                self.assertEqual(result, expected)
    
    def test_invalid_formats(self):
        invalid_cases = [
            "1,234,567.89",  # US format
            "1.234.567,89,00",  # Too many decimals
            "abc123",  # Invalid characters
            "",  # Empty string
        ]
        
        for invalid_input in invalid_cases:
            with self.subTest(input=invalid_input):
                with self.assertRaises(ValueError):
                    convert_brazilian_amount_to_float(invalid_input)

if __name__ == '__main__':
    unittest.main()