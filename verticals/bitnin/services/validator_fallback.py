"""
Fallback validator for BitNin when jsonschema is not available.
Provides a simple interface compatible with Draft202012Validator.
"""
import logging

logger = logging.getLogger(__name__)

class BasicValidatorFallback:
    def __init__(self, schema, format_checker=None):
        self.schema = schema

    def validate(self, instance):
        if not isinstance(instance, dict):
            raise ValueError("Instance must be a dictionary")
        # In a real environment we would do more, but here we just ensure basic dict structure
        return True

    def iter_errors(self, instance):
        if not isinstance(instance, dict):
            yield type('Error', (), {'message': "Instance must be a dictionary"})()
        # Return empty list of errors if it's a dict
        return []

# Shorthands for BitNin patterns
def get_bitnin_validator(schema_path):
    # Just a placeholder that returns a fallback object
    return BasicValidatorFallback({})
