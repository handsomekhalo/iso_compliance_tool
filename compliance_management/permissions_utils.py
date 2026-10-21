from compliance_management.models import Bank


def _bank_for_user(user):
    """
    Resolve the Bank for a user.
    - Normal staff: Bank linked via user OneToOne
    - Super admin with bank=None on UserRole: may have no bank — callers handle 404
    """
    try:
        return user.bank
    except Exception:
        try:
            return Bank.objects.get(user=user)
        except Bank.DoesNotExist:
            return None