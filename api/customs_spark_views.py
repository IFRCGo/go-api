"""
Customs regulations and updates API views.
"""

import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import CountryCustomsSnapshot
from api.serializers import (
    CountryCustomsSnapshotSerializer,
    CountryRegulationSerializer,
)

from .customs_ai_service import CustomsAIService
from .customs_data_loader import load_customs_regulations

logger = logging.getLogger(__name__)


class CustomsRegulationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = load_customs_regulations()
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"detail": "Failed to load customs regulations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomsRegulationCountryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, country):
        try:
            data = load_customs_regulations()

            for c in data.get("countries", []):
                if c.get("country", "").lower() == country.lower():
                    serializer = CountryRegulationSerializer(c)
                    return Response(serializer.data, status=status.HTTP_200_OK)

            return Response({"detail": "Country not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(
                {"detail": "Failed to load country regulations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomsUpdatesView(APIView):
    """
    List available AI-generated customs updates.
    GET /api/v2/customs-ai-updates/ - List all countries with current snapshots
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            snapshots = CountryCustomsSnapshot.objects.filter(is_current=True).order_by("country_name")
            serializer = CountryCustomsSnapshotSerializer(snapshots, many=True)
            return Response({"results": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to list customs updates: {str(e)}")
            return Response(
                {"detail": "Failed to load customs updates"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomsUpdatesCountryView(APIView):
    """
    Get or generate AI-powered customs update for a country.
    GET /api/v2/customs-ai-updates/<country>/ - Get snapshot, or generate if doesn't exist
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, country):
        try:
            country_name = country.strip()

            existing_snapshot = CountryCustomsSnapshot.objects.filter(
                country_name__iexact=country_name,
                is_current=True,
            ).first()

            if existing_snapshot:
                logger.info(f"Returning existing snapshot for {country_name}")
                serializer = CountryCustomsSnapshotSerializer(existing_snapshot)
                return Response(serializer.data, status=status.HTTP_200_OK)

            logger.info(f"No snapshot found for {country_name}, validating and generating...")

            is_valid, error_msg = CustomsAIService.validate_country_name(country_name)
            if not is_valid:
                logger.warning(f"Invalid country name: {country_name}")
                return Response(
                    {"detail": error_msg or f"'{country_name}' is not a recognized country."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info(f"Country '{country_name}' validation passed, generating snapshot...")
            snapshot = CustomsAIService.generate_customs_snapshot(country_name)

            if snapshot.status == "failed":
                logger.error(f"Generation failed for {country_name}: {snapshot.error_message}")
                return Response(
                    {
                        "detail": snapshot.error_message or "Failed to generate customs update",
                        "country": country_name,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            serializer = CountryCustomsSnapshotSerializer(snapshot)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            # Incase another request created the snapshot while we were generating
            # Return the existing snapshot instead
            logger.info(f"Race condition detected for {country}, returning existing snapshot")
            existing_snapshot = CountryCustomsSnapshot.objects.filter(
                country_name__iexact=country.strip(),
                is_current=True,
            ).first()
            if existing_snapshot:
                serializer = CountryCustomsSnapshotSerializer(existing_snapshot)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                {"detail": "An error occurred while processing customs update"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.error(f"Exception in customs update endpoint for {country}: {str(e)}")
            return Response(
                {"detail": "An error occurred while processing customs update"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, country):
        """
        Deactivate the current customs snapshot for a country.
        DELETE /api/v2/customs-ai-updates/<country>/ - Mark current snapshot as inactive
        """
        try:
            country_name = country.strip()

            current_snapshot = CountryCustomsSnapshot.objects.filter(
                country_name__iexact=country_name,
                is_current=True,
            ).first()

            if not current_snapshot:
                return Response(
                    {"detail": f"No active customs data found for '{country_name}'"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            current_snapshot.is_current = False
            current_snapshot.save(update_fields=["is_current"])

            logger.info(f"Deactivated current snapshot for {country_name} (id={current_snapshot.pk})")
            return Response(
                {"detail": f"Successfully deactivated customs snapshot for '{country_name}'"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Failed to deactivate customs data for {country}: {str(e)}")
            return Response(
                {"detail": "Failed to deactivate customs data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
