"""Gestion role groups (Django auth Groups).

These are the internal staff roles. Field users (Agent / Warehouseman) are NOT
Django users — they are the separate FieldUser model authenticated on the public app.
"""

INVENTORY_RESPONSIBLE = "Inventory Responsible"
AUDIT = "Audit"
CDG = "CDG"

ALL_GROUPS = (INVENTORY_RESPONSIBLE, AUDIT, CDG)
