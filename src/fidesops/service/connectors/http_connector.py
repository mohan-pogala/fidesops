import json

import logging
from typing import Dict, Any, List, Optional
import requests

from fidesops.common_exceptions import ClientUnsuccessfulException
from fidesops.graph.traversal import TraversalNode
from fidesops.models.connectionconfig import ConnectionTestStatus
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.connection_configuration import HttpsSchema

from fidesops.service.connectors.base_connector import BaseConnector
from fidesops.service.connectors.query_config import QueryConfig
from fidesops.util.collection_util import Row

logger = logging.getLogger(__name__)


class HTTPSConnector(BaseConnector[None]):
    """HTTP Connector - for connecting to second and third-party endpoints"""

    def build_uri(self) -> str:
        """
        Returns URL stored on ConnectionConfig
        """
        config = HttpsSchema(**self.configuration.secrets or {})
        return config.url

    def build_authorization_header(self) -> Dict[str, str]:
        """
        Returns Authorization headers
        """
        config = HttpsSchema(**self.configuration.secrets or {})
        return {"Authorization": config.authorization}

    def execute(
        self,
        request_body: Dict[str, Any],
        response_expected: bool,
        additional_headers: Dict[str, Any] = {},
    ) -> Optional[Dict[str, Any]]:
        """Calls a client-defined endpoint and returns the data that it responds with"""
        config = HttpsSchema(**self.configuration.secrets or {})
        headers = self.build_authorization_header()
        headers.update(additional_headers)

        try:
            response = requests.post(url=config.url, headers=headers, json=request_body)
        except requests.ConnectionError:
            logger.info("Requests connection error received.")
            raise ClientUnsuccessfulException(status_code=500)

        if not response_expected:
            return {}

        if not response.ok:
            logger.error("Invalid response received from webhook.")
            raise ClientUnsuccessfulException(status_code=response.status_code)
        return json.loads(response.text)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Override to skip connection test
        """
        return ConnectionTestStatus.skipped

    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve data in a connector dependent way based on input data.

        The input data is expected to include a key and list of values for
        each input key that may be queried on.

        TODO: implement when HTTPS Connectors can be part of the traversal.
        """

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated

        TODO: implement when HTTPS Connectors can be part of the traversal.
        """

    def create_client(self) -> None:
        """Not required for this type"""
        return None

    def close(self) -> None:
        """Not required for this type"""
