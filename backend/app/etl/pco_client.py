"""
Planning Center Online API client with authentication, pagination, rate limiting, and retry logic.
"""
import requests
import base64
import time
from typing import Dict, List, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


class PCOClient:
    """Client for interacting with Planning Center Online API"""

    BASE_URL = "https://api.planningcenteronline.com"

    def __init__(self, app_id: str, secret: str):
        """
        Initialize PCO client with credentials.

        Args:
            app_id: Planning Center App ID
            secret: Planning Center Secret Key
        """
        self.app_id = app_id
        self.secret = secret
        self._session = None
        self._setup_session()

    def _setup_session(self):
        """Set up requests session with authentication and retry strategy"""
        self._session = requests.Session()

        # Create Basic Auth header
        combined = f"{self.app_id}:{self.secret}"
        encoded_credentials = base64.b64encode(combined.encode()).decode()
        self._session.headers.update({
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        })

        # Retry strategy for rate limits and server errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )

        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limit (429) responses"""
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            logger.warning(f"Rate limit hit. Waiting {retry_after} seconds...")
            time.sleep(retry_after)

    def get(self, endpoint: str, params: Optional[Dict] = None, include: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Make GET request to Planning Center API.

        Args:
            endpoint: API endpoint (e.g., '/people/v2/people')
            params: Query parameters
            include: List of related resources to include

        Returns:
            JSON response as dictionary
        """
        import time as time_module
        start_time = time_module.time()
        url = f"{self.BASE_URL}{endpoint}"

        if params is None:
            params = {}

        if include:
            params['include'] = ','.join(include)

        logger.info(f"[PCO API] GET {endpoint} - params: {params}, includes: {include}")

        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            try:
                logger.debug(f"[PCO API] Attempt {retry_count + 1}/{max_retries} - {url}")
                response = self._session.get(url, params=params, timeout=30)
                elapsed = time_module.time() - start_time

                logger.info(f"[PCO API] Response {response.status_code} in {elapsed:.2f}s - {endpoint}")

                if response.status_code == 429:
                    logger.warning(f"[PCO API] Rate limit hit (429) for {endpoint}")
                    self._handle_rate_limit(response)
                    retry_count += 1
                    continue

                response.raise_for_status()
                json_data = response.json()

                # Log response size
                data_count = len(json_data.get('data', []))
                included_count = len(json_data.get('included', []))
                logger.info(f"[PCO API] Received {data_count} data items, {included_count} included items from {endpoint}")

                return json_data

            except requests.exceptions.RequestException as e:
                retry_count += 1
                elapsed = time_module.time() - start_time
                if retry_count >= max_retries:
                    logger.error(f"[PCO API] Failed to fetch {url} after {max_retries} retries ({elapsed:.2f}s): {e}")
                    raise
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"[PCO API] Request failed after {elapsed:.2f}s, retrying in {wait_time}s (attempt {retry_count}/{max_retries}): {e}")
                time.sleep(wait_time)

        raise Exception(f"Failed to fetch {url} after {max_retries} retries")

    def get_all_pages(self, endpoint: str, params: Optional[Dict] = None,
                     include: Optional[List[str]] = None,
                     per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch all pages of a paginated endpoint.

        Args:
            endpoint: API endpoint
            params: Query parameters
            include: List of related resources to include
            per_page: Number of records per page (max 100)

        Returns:
            List of all records from all pages
        """
        import time as time_module
        start_time = time_module.time()
        all_data = []
        offset = 0
        page_num = 0

        if params is None:
            params = {}

        params['per_page'] = min(per_page, 100)  # API max is 100

        logger.info(f"[PCO API] Starting pagination for {endpoint} (per_page={params['per_page']})")

        while True:
            page_num += 1
            page_start = time_module.time()
            params['offset'] = offset

            logger.info(f"[PCO API] Fetching page {page_num} (offset={offset}) for {endpoint}")
            response = self.get(endpoint, params=params, include=include)

            # Extract data from JSON:API response
            data_items = response.get('data', [])
            if not data_items:
                logger.info(f"[PCO API] No data items in page {page_num}, ending pagination")
                break

            all_data.extend(data_items)
            page_elapsed = time_module.time() - page_start
            total_elapsed = time_module.time() - start_time

            logger.info(f"[PCO API] Page {page_num} complete: {len(data_items)} items, {len(all_data)} total so far ({page_elapsed:.2f}s page, {total_elapsed:.2f}s total)")

            # Check if there's a next page
            links = response.get('links', {})
            if 'next' not in links or not links['next']:
                logger.info(f"[PCO API] No next page link, pagination complete for {endpoint}")
                break

            offset += len(data_items)

            # Small delay to respect rate limits
            time.sleep(0.1)

        total_elapsed = time_module.time() - start_time
        logger.info(f"[PCO API] Pagination complete for {endpoint}: {len(all_data)} total records in {page_num} pages ({total_elapsed:.2f}s)")

        return all_data

    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test the connection to Planning Center API.

        Returns:
            (success: bool, error_message: str or None)
        """
        try:
            # Try to fetch a simple endpoint
            response = self.get('/people/v2/people', params={'per_page': 1})
            return True, None
        except Exception as e:
            return False, str(e)
