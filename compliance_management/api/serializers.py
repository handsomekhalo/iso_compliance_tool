from rest_framework import serializers
from django.contrib.auth.models import User

from compliance_management.models import AMLAlert, Bank, ISOReconciliationLog, SandboxUser, ZARPBurnEvent, ZARPMintEvent


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_superuser"]


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = "__all__"


class ISOReconciliationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOReconciliationLog
        fields = "__all__"


class ZARPMintEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZARPMintEvent
        fields = "__all__"


class ZARPBurnEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZARPBurnEvent
        fields = "__all__"


class SandboxUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SandboxUser
        fields = "__all__"


class AMLAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AMLAlert
        fields = "__all__"
