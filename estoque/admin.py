from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Entrega, Familia, ItemEntrega, LoteEstoque, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Cesta Certa", {"fields": ("perfil", "tentativas_falhas", "bloqueado_ate")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Cesta Certa", {"fields": ("perfil",)}),)
    list_display = ("username", "perfil", "is_staff", "bloqueado_ate")


@admin.register(Familia)
class FamiliaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "ativa", "criada_em")
    search_fields = ("codigo", "documento")


@admin.register(LoteEstoque)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "produto", "validade", "saldo_kg", "priorizado")
    list_filter = ("priorizado",)


admin.site.register(Entrega)
admin.site.register(ItemEntrega)
