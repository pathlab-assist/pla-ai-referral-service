"""Test name fuzzy matching service using test-catalog-service."""
import httpx

from app.config import settings
from app.core.logging import get_logger
from app.schemas.referral import MatchedTest
from app.services.oauth_client import OAuthClient

logger = get_logger(__name__)


class TestMatcherService:
    """Service for fuzzy matching test names to catalog via test-catalog-service."""

    def __init__(self, organization_id: str = "dev-org") -> None:
        """Initialize test matcher service.

        Args:
            organization_id: Organization ID for multi-tenancy (from JWT context)
        """
        self.organization_id = organization_id
        self.catalog_url = settings.test_catalog_service_url
        self.oauth_client = OAuthClient()

    async def match_test(self, test_name: str) -> MatchedTest:
        """Match a single test name to the catalog.

        Calls test-catalog-service search endpoint and converts search score
        to confidence (0.0-1.0).

        Args:
            test_name: Test name to match

        Returns:
            MatchedTest with confidence score
        """
        test_stripped = test_name.strip()

        # Skip empty strings
        if not test_stripped:
            return MatchedTest(
                original=test_name,
                matched=test_name,
                test_id=test_name,
                confidence=0.0,
            )

        try:
            # Get OAuth token for service-to-service auth
            access_token = await self.oauth_client.get_access_token()

            headers = {"X-Organization-Code": self.organization_id}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

            async with httpx.AsyncClient() as client:
                # Call test-catalog-service search endpoint
                response = await client.get(
                    f"{self.catalog_url}/api/v1/tests",
                    params={"q": test_stripped},
                    headers=headers,
                    timeout=5.0,
                )

                if response.status_code != 200:
                    logger.warning(
                        "Test catalog search failed",
                        status_code=response.status_code,
                        test_name=test_stripped,
                    )
                    # Return original with low confidence
                    return MatchedTest(
                        original=test_name,
                        matched=test_name,
                        test_id=test_name,
                        confidence=0.3,
                    )

                data = response.json()
                tests = data.get("tests", [])

                if not tests:
                    # No match found - return original with low confidence
                    logger.debug("No test match found", test_name=test_stripped)
                    return MatchedTest(
                        original=test_name,
                        matched=test_name,
                        test_id=test_name,
                        confidence=0.3,
                    )

                # Use first result (highest search score)
                best_match = tests[0]

                # Convert search score (0-100) to confidence (0.0-1.0)
                # Score ranges from test-catalog-service:
                # - Exact code match: 100
                # - Exact alias: 90
                # - Partial code: 50
                # - Partial alias: 40
                # - Name match: 30
                # - Medicare item: 20
                # - Description: 10
                search_score = best_match.get("searchScore", 0)
                confidence = min(search_score / 100.0, 1.0)

                return MatchedTest(
                    original=test_name,
                    matched=best_match.get("name", test_name),
                    test_id=best_match.get("code", test_name),
                    confidence=confidence,
                )

        except httpx.TimeoutException:
            logger.error("Test catalog service timeout", test_name=test_stripped)
            # Return original with low confidence
            return MatchedTest(
                original=test_name,
                matched=test_name,
                test_id=test_name,
                confidence=0.2,
            )
        except Exception as e:
            logger.error(
                "Test matching error",
                test_name=test_stripped,
                error=str(e),
            )
            # Return original with low confidence
            return MatchedTest(
                original=test_name,
                matched=test_name,
                test_id=test_name,
                confidence=0.2,
            )

    async def match_tests(self, test_names: list[str]) -> list[MatchedTest]:
        """Match multiple test names to the catalog using batch endpoint.

        Uses the new POST /api/v1/tests/match batch endpoint for improved
        performance (1 request vs N requests).

        Args:
            test_names: List of test names to match (1-50 items)

        Returns:
            List of matched tests with confidence scores
        """
        if not test_names:
            return []

        # Use batch matching endpoint for better performance
        try:
            # Get OAuth token for service-to-service auth
            access_token = await self.oauth_client.get_access_token()

            headers = {"X-Organization-Code": self.organization_id}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.catalog_url}/api/v1/tests/match",
                    json={
                        "testNames": test_names,
                        "region": "DEFAULT",  # Can be made configurable
                    },
                    headers=headers,
                    timeout=10.0,  # Longer timeout for batch operation
                )

                if response.status_code != 200:
                    logger.warning(
                        "Batch test matching failed, falling back to individual matches",
                        status_code=response.status_code,
                        test_count=len(test_names),
                    )
                    # Fallback to individual matching
                    import asyncio

                    tasks = [self.match_test(test_name) for test_name in test_names]
                    return await asyncio.gather(*tasks)

                data = response.json()
                matches = data.get("matches", [])

                # Convert batch response to MatchedTest objects
                results = []
                for match in matches:
                    # Convert search score (0-100) to confidence (0.0-1.0)
                    search_score = match.get("searchScore", 0)
                    confidence = min(search_score / 100.0, 1.0)

                    # If no match found, use original test name
                    if not match.get("matched", False):
                        results.append(
                            MatchedTest(
                                original=match.get("query", ""),
                                matched=match.get("query", ""),
                                test_id=match.get("query", ""),
                                confidence=0.3,
                            )
                        )
                    else:
                        results.append(
                            MatchedTest(
                                original=match.get("query", ""),
                                matched=match.get("name", ""),
                                test_id=match.get("code", ""),
                                confidence=confidence,
                            )
                        )

                logger.info(
                    "Batch test matching complete",
                    total_tests=len(test_names),
                    matched_count=sum(1 for m in matches if m.get("matched", False)),
                )

                return results

        except httpx.TimeoutException:
            logger.error(
                "Batch test matching timeout, falling back to individual matches",
                test_count=len(test_names),
            )
            # Fallback to individual matching
            import asyncio

            tasks = [self.match_test(test_name) for test_name in test_names]
            return await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(
                "Batch test matching error, falling back to individual matches",
                test_count=len(test_names),
                error=str(e),
            )
            # Fallback to individual matching
            import asyncio

            tasks = [self.match_test(test_name) for test_name in test_names]
            return await asyncio.gather(*tasks)
