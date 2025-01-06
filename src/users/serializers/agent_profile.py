from rest_framework import serializers

from users.models import AgentProfile, AgentSettlementAccount

class AgentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentProfile
        exclude = [ 'user', ]


class UpdateAgentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentProfile
        fields = [ 'profile_image', ]


class AgentSettlementAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentSettlementAccount
        exclude = [ 'id', 'user', ]

    def create(self, validated_data):
        agent = self.context['agent']

        return AgentSettlementAccount.objects.create(
            user=agent,
            **validated_data,
        )
