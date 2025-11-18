"""
Data cleaning pipeline for ScrapeMaster
Provides various data cleaning and transformation utilities
"""
import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import html

logger = logging.getLogger(__name__)


class DataCleaner:
    """Main data cleaning class"""

    @staticmethod
    def clean_text(text: str, options: Dict[str, bool] = None) -> str:
        """
        Clean text data with various options

        Options:
        - strip_whitespace: Remove extra whitespace (default: True)
        - remove_newlines: Remove newline characters (default: False)
        - lowercase: Convert to lowercase (default: False)
        - remove_punctuation: Remove punctuation (default: False)
        - decode_html: Decode HTML entities (default: True)
        - remove_urls: Remove URLs from text (default: False)
        - remove_numbers: Remove numbers (default: False)
        """
        if not text:
            return ""

        if options is None:
            options = {}

        # Set defaults
        options.setdefault('strip_whitespace', True)
        options.setdefault('decode_html', True)
        options.setdefault('remove_newlines', False)
        options.setdefault('lowercase', False)
        options.setdefault('remove_punctuation', False)
        options.setdefault('remove_urls', False)
        options.setdefault('remove_numbers', False)

        cleaned = text

        # Decode HTML entities
        if options['decode_html']:
            cleaned = html.unescape(cleaned)

        # Remove URLs
        if options['remove_urls']:
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            cleaned = re.sub(url_pattern, '', cleaned)

        # Remove newlines
        if options['remove_newlines']:
            cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')

        # Strip whitespace
        if options['strip_whitespace']:
            cleaned = ' '.join(cleaned.split())
            cleaned = cleaned.strip()

        # Lowercase
        if options['lowercase']:
            cleaned = cleaned.lower()

        # Remove punctuation
        if options['remove_punctuation']:
            cleaned = re.sub(r'[^\w\s]', '', cleaned)

        # Remove numbers
        if options['remove_numbers']:
            cleaned = re.sub(r'\d+', '', cleaned)

        return cleaned

    @staticmethod
    def clean_url(url: str, options: Dict[str, bool] = None) -> str:
        """
        Clean and normalize URL

        Options:
        - remove_params: Remove query parameters (default: False)
        - remove_fragment: Remove fragment identifier (default: True)
        - lowercase: Convert to lowercase (default: True)
        - remove_trailing_slash: Remove trailing slash (default: True)
        """
        if not url:
            return ""

        if options is None:
            options = {}

        options.setdefault('remove_params', False)
        options.setdefault('remove_fragment', True)
        options.setdefault('lowercase', True)
        options.setdefault('remove_trailing_slash', True)

        try:
            parsed = urlparse(url)

            # Rebuild URL
            scheme = parsed.scheme
            netloc = parsed.netloc.lower() if options['lowercase'] else parsed.netloc
            path = parsed.path

            # Remove trailing slash
            if options['remove_trailing_slash'] and path.endswith('/') and len(path) > 1:
                path = path.rstrip('/')

            # Build cleaned URL
            if options['remove_params'] and options['remove_fragment']:
                cleaned = f"{scheme}://{netloc}{path}"
            elif options['remove_params']:
                cleaned = f"{scheme}://{netloc}{path}#{parsed.fragment}"
            elif options['remove_fragment']:
                query = f"?{parsed.query}" if parsed.query else ""
                cleaned = f"{scheme}://{netloc}{path}{query}"
            else:
                cleaned = url

            return cleaned

        except Exception as e:
            logger.error(f"Error cleaning URL {url}: {e}")
            return url

    @staticmethod
    def validate_data(data: str, data_type: str) -> bool:
        """
        Validate data based on type

        Returns True if data is valid, False otherwise
        """
        if not data:
            return False

        try:
            if data_type == "Text":
                # Text should have at least 3 characters
                return len(data.strip()) >= 3

            elif data_type == "Links":
                # Links should be valid URLs
                parsed = urlparse(data)
                return bool(parsed.scheme and parsed.netloc)

            elif data_type == "Images":
                # Images should be valid URLs or paths
                if data.startswith('/'):
                    return True
                parsed = urlparse(data)
                return bool(parsed.scheme and parsed.netloc)

            elif data_type == "Videos":
                # Videos should be valid URLs or paths
                if data.startswith('/'):
                    return True
                parsed = urlparse(data)
                return bool(parsed.scheme and parsed.netloc)

            return True

        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return False

    @staticmethod
    def remove_duplicates(data_list: List[str], case_sensitive: bool = True) -> List[str]:
        """
        Remove duplicates while preserving order

        Args:
            data_list: List of data items
            case_sensitive: Whether to consider case when checking duplicates
        """
        if not case_sensitive:
            seen = set()
            result = []
            for item in data_list:
                item_lower = item.lower()
                if item_lower not in seen:
                    seen.add(item_lower)
                    result.append(item)
            return result
        else:
            seen = set()
            result = []
            for item in data_list:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

    @staticmethod
    def filter_by_length(data_list: List[str], min_length: int = None,
                        max_length: int = None) -> List[str]:
        """Filter data by length constraints"""
        result = []
        for item in data_list:
            item_len = len(item)
            if min_length and item_len < min_length:
                continue
            if max_length and item_len > max_length:
                continue
            result.append(item)
        return result

    @staticmethod
    def filter_by_pattern(data_list: List[str], pattern: str,
                         include: bool = True) -> List[str]:
        """
        Filter data by regex pattern

        Args:
            data_list: List of data items
            pattern: Regex pattern to match
            include: If True, include matches; if False, exclude matches
        """
        try:
            regex = re.compile(pattern)
            if include:
                return [item for item in data_list if regex.search(item)]
            else:
                return [item for item in data_list if not regex.search(item)]
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return data_list


class DataCleaningPipeline:
    """Pipeline for applying multiple cleaning steps"""

    def __init__(self):
        self.cleaner = DataCleaner()
        self.steps = []

    def add_step(self, step_type: str, options: Dict[str, Any] = None):
        """Add a cleaning step to the pipeline"""
        self.steps.append({
            'type': step_type,
            'options': options or {}
        })
        return self

    def clean(self, data_list: List[str], data_type: str) -> List[str]:
        """
        Apply all cleaning steps to data

        Args:
            data_list: List of data items to clean
            data_type: Type of data (Text, Links, Images, Videos)
        """
        cleaned_data = data_list.copy()

        for step in self.steps:
            step_type = step['type']
            options = step['options']

            logger.info(f"Applying cleaning step: {step_type}")

            if step_type == 'clean_text' and data_type == 'Text':
                cleaned_data = [
                    self.cleaner.clean_text(item, options)
                    for item in cleaned_data
                ]

            elif step_type == 'clean_url' and data_type in ['Links', 'Images', 'Videos']:
                cleaned_data = [
                    self.cleaner.clean_url(item, options)
                    for item in cleaned_data
                ]

            elif step_type == 'validate':
                cleaned_data = [
                    item for item in cleaned_data
                    if self.cleaner.validate_data(item, data_type)
                ]

            elif step_type == 'remove_duplicates':
                case_sensitive = options.get('case_sensitive', True)
                cleaned_data = self.cleaner.remove_duplicates(
                    cleaned_data, case_sensitive
                )

            elif step_type == 'filter_by_length':
                min_length = options.get('min_length')
                max_length = options.get('max_length')
                cleaned_data = self.cleaner.filter_by_length(
                    cleaned_data, min_length, max_length
                )

            elif step_type == 'filter_by_pattern':
                pattern = options.get('pattern')
                include = options.get('include', True)
                if pattern:
                    cleaned_data = self.cleaner.filter_by_pattern(
                        cleaned_data, pattern, include
                    )

        logger.info(f"Cleaning complete: {len(data_list)} -> {len(cleaned_data)} items")
        return cleaned_data


def create_default_pipeline(data_type: str) -> DataCleaningPipeline:
    """Create a default cleaning pipeline based on data type"""
    pipeline = DataCleaningPipeline()

    if data_type == "Text":
        pipeline.add_step('clean_text', {
            'strip_whitespace': True,
            'decode_html': True,
            'remove_newlines': False
        })
        pipeline.add_step('filter_by_length', {'min_length': 3})
        pipeline.add_step('validate')
        pipeline.add_step('remove_duplicates', {'case_sensitive': False})

    elif data_type in ["Links", "Images", "Videos"]:
        pipeline.add_step('clean_url', {
            'remove_fragment': True,
            'lowercase': True,
            'remove_trailing_slash': True
        })
        pipeline.add_step('validate')
        pipeline.add_step('remove_duplicates', {'case_sensitive': False})

    return pipeline
