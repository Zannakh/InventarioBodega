from rest_framework.permissions import BasePermission, SAFE_METHODS

# ────────────────────────────────
# Utilidad base
# ────────────────────────────────
def _in_group(user, group_name: str) -> bool:
    """Devuelve True si el usuario pertenece al grupo indicado."""
    return user and user.is_authenticated and user.groups.filter(name=group_name).exists()


# ────────────────────────────────
# Permisos individuales por rol
# ────────────────────────────────
class IsAdmin(BasePermission):
    """Administrador o superusuario → acceso total."""
    def has_permission(self, request, view):
        return request.user.is_superuser or _in_group(request.user, "Administrador")


class VendedorPermisos(BasePermission):
    """
    Vendedor → lectura global + POST únicamente en movimientos.
    """
    def has_permission(self, request, view):
        if not _in_group(request.user, "Vendedor"):
            return False

        # Lectura total (GET/HEAD/OPTIONS)
        if request.method in SAFE_METHODS:
            return True

        # Crear movimientos (POST)
        basename = getattr(view, "basename", "")  # DRF la define al registrar en router
        return request.method == "POST" and "movimiento" in str(basename).lower()


class ConsultorSoloLectura(BasePermission):
    """Consultor → solo lectura (GET/HEAD/OPTIONS)."""
    def has_permission(self, request, view):
        return _in_group(request.user, "Consultor") and request.method in SAFE_METHODS


# ────────────────────────────────
# Permiso combinado (recomendado)
# ────────────────────────────────
class RolCompositePermission(BasePermission):
    """
    Control centralizado:
    - Admin / superuser: CRUD total.
    - Vendedor: lectura total + creación de movimientos.
    - Consultor: solo lectura.
    - Otros: sin acceso.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Orden jerárquico: Admin → Vendedor → Consultor
        if IsAdmin().has_permission(request, view):
            return True
        if VendedorPermisos().has_permission(request, view):
            return True
        if ConsultorSoloLectura().has_permission(request, view):
            return True

        # Por defecto, solo lectura para métodos seguros
        return request.method in SAFE_METHODS
