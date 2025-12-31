"""
Dynamic discovery of Planning Center API endpoints, resources, and schemas.
"""
import json
import logging
from typing import Dict, List, Optional, Any, Set
from app.etl.pco_client import PCOClient

logger = logging.getLogger(__name__)


class MetadataDiscovery:
    """Discover available endpoints, resources, and schemas from Planning Center API"""

    # Known Planning Center services
    KNOWN_SERVICES = [
        'people',
        'check-ins',
        'services',
        'groups',
        'giving',
        'calendar',
        'resources'
    ]

    def __init__(self, client: PCOClient):
        """
        Initialize metadata discovery.

        Args:
            client: PCOClient instance
        """
        self.client = client
        self._cache = {}

    def discover_services(self) -> List[str]:
        """
        Discover available services/endpoints.

        Returns:
            List of service names
        """
        available_services = []

        for service in self.KNOWN_SERVICES:
            try:
                endpoint = f'/{service}/v2'
                response = self.client.get(endpoint, params={'per_page': 1})
                available_services.append(service)
                logger.info(f"Discovered service: {service}")
            except Exception as e:
                logger.debug(f"Service {service} not available: {e}")

        return available_services

    def discover_resources(self, service: str) -> List[Dict[str, Any]]:
        """
        Discover available resources within a service.

        Args:
            service: Service name (e.g., 'people', 'check-ins')

        Returns:
            List of resource dictionaries with name, endpoint, etc.
        """
        resources = []

        common_resources = {
            'people': ['people', 'households', 'emails', 'phone_numbers', 'addresses'],
            'check-ins': ['check_ins', 'event_times', 'events', 'locations'],
            'services': ['plans', 'series', 'songs', 'arrangements'],
            'groups': ['groups', 'group_types', 'memberships'],
            'giving': ['donations', 'funds', 'batches'],
            'calendar': ['events', 'event_times'],
            'resources': ['resources', 'resource_requests']
        }

        known_resources = common_resources.get(service, [])

        for resource in known_resources:
            try:
                endpoint = f'/{service}/v2/{resource}'
                response = self.client.get(endpoint, params={'per_page': 1})

                meta = response.get('meta', {})
                total_count = meta.get('total_count', 0)

                resources.append({
                    'name': resource,
                    'endpoint': endpoint,
                    'service': service,
                    'total_count': total_count,
                    'available': True
                })
                logger.info(f"Discovered resource: {service}/{resource}")
            except Exception as e:
                logger.debug(f"Resource {service}/{resource} not available: {e}")

        return resources

    def discover_schema(self, endpoint: str, include: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Discover the schema of a resource by examining sample data.

        Args:
            endpoint: API endpoint (e.g., '/people/v2/people')
            include: List of related resources to include

        Returns:
            Schema dictionary with attributes, relationships, etc.
        """
        try:
            response = self.client.get(endpoint, params={'per_page': 1}, include=include)

            data_items = response.get('data', [])
            included_items = response.get('included', [])

            if not data_items:
                return {'attributes': {}, 'relationships': {}, 'included_types': []}

            sample_item = data_items[0]
            attributes = sample_item.get('attributes', {})
            relationships = sample_item.get('relationships', {})

            included_types = set()
            for item in included_items:
                included_types.add(item.get('type', ''))

            schema = {
                'attributes': list(attributes.keys()),
                'attribute_types': self._infer_types(attributes),
                'relationships': list(relationships.keys()),
                'included_types': list(included_types),
                'id_type': sample_item.get('id'),
                'type': sample_item.get('type')
            }

            return schema

        except Exception as e:
            logger.error(f"Failed to discover schema for {endpoint}: {e}")
            return {'attributes': {}, 'relationships': {}, 'included_types': []}

    def _infer_types(self, attributes: Dict[str, Any]) -> Dict[str, str]:
        """Infer Python/SQL types from attribute values."""
        type_map = {}

        for key, value in attributes.items():
            if value is None:
                type_map[key] = 'string'
            elif isinstance(value, bool):
                type_map[key] = 'boolean'
            elif isinstance(value, int):
                type_map[key] = 'integer'
            elif isinstance(value, float):
                type_map[key] = 'float'
            elif isinstance(value, str):
                if 'at' in key.lower() or 'date' in key.lower() or 'time' in key.lower():
                    type_map[key] = 'datetime'
                else:
                    type_map[key] = 'string'
            elif isinstance(value, list):
                type_map[key] = 'array'
            elif isinstance(value, dict):
                type_map[key] = 'object'
            else:
                type_map[key] = 'string'

        return type_map

    def discover_resources_comprehensive(self, service: str) -> List[Dict[str, Any]]:
        """
        Comprehensively discover all resources within a service.

        Args:
            service: Service name (e.g., 'people', 'check-ins')

        Returns:
            List of resource dictionaries with name, endpoint, etc.
        """
        resources = []
        discovered_endpoints = set()

        common_resources = {
            'people': ['people', 'households', 'emails', 'phone_numbers', 'addresses',
                      'tabs', 'field_definitions', 'field_data', 'lists', 'workflows'],
            'check-ins': ['check_ins', 'event_times', 'events', 'locations', 'event_periods'],
            'services': ['plans', 'series', 'songs', 'arrangements', 'items', 'plan_times'],
            'groups': ['groups', 'group_types', 'memberships', 'coaches'],
            'giving': ['donations', 'funds', 'batches', 'designations'],
            'calendar': ['events', 'event_times', 'calendars'],
            'resources': ['resources', 'resource_requests', 'resource_bookings']
        }

        known_resources = common_resources.get(service, [])

        for resource in known_resources:
            endpoint = f'/{service}/v2/{resource}'
            if endpoint in discovered_endpoints:
                continue

            try:
                response = self.client.get(endpoint, params={'per_page': 1})
                meta = response.get('meta', {})
                total_count = meta.get('total_count', 0)

                resources.append({
                    'name': resource,
                    'endpoint': endpoint,
                    'service': service,
                    'total_count': total_count,
                    'available': True
                })
                discovered_endpoints.add(endpoint)
                logger.info(f"Discovered resource: {service}/{resource} (count: {total_count})")
            except Exception as e:
                logger.debug(f"Resource {service}/{resource} not available: {e}")

        return resources

    def get_available_includes(self, endpoint: str) -> List[str]:
        """
        Get available include options for an endpoint.

        Args:
            endpoint: API endpoint

        Returns:
            List of available include options
        """
        try:
            response = self.client.get(endpoint, params={'per_page': 1})
            data_items = response.get('data', [])

            if not data_items:
                return []

            sample_item = data_items[0]
            relationships = sample_item.get('relationships', {})

            return list(relationships.keys())

        except Exception as e:
            logger.error(f"Failed to get available includes for {endpoint}: {e}")
            return []
