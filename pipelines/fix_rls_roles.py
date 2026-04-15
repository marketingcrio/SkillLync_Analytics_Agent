# ============================================================
# Fabric Notebook — List & Fix RLS Roles
# ------------------------------------------------------------
# Use this when PBI throws:
#   "The combination of active roles results in a dynamic
#    security configuration that is not consistent."
#
# Typical cause: a pre-existing RLS role references a column or
# relationship that got renamed / dropped during the rebuild.
#
# RLS editing is no longer available in PBI Service UI — you
# either need PBI Desktop, or this notebook.
# ============================================================

import sempy.fabric as fabric

# Set to the exact semantic model name that throws the error.
# Get it from: workspace → three dots on the dataset → Rename
DATASET_NAME = "Crio - Past Data Reports"   # <-- CHANGE if different

# Dry run first. Flip to True only after reviewing output.
DELETE_ALL_ROLES = False

# Or list specific role names to delete (case-sensitive):
ROLES_TO_DELETE = []   # e.g. ["BDA-level RLS", "DM only"]


# ── Step 1: list all roles and their filters ────────────────

tom = fabric.create_tom_server(readonly=True)
try:
    db = tom.Databases.GetByName(DATASET_NAME)
    model = db.Model

    roles = list(model.Roles)
    print(f"Semantic model: {DATASET_NAME}")
    print(f"Roles defined : {len(roles)}")
    print("=" * 60)

    for r in roles:
        print(f"\n  Role: {r.Name}")
        print(f"    Members: {r.Members.Count}")
        tps = list(r.TablePermissions)
        if not tps:
            print("    (no table filters — role is empty)")
        for tp in tps:
            tbl = tp.Table.Name if tp.Table else "(unknown)"
            expr = (tp.FilterExpression or "").strip()
            if expr:
                print(f"    Table [{tbl}]:")
                print(f"      {expr}")
            else:
                print(f"    Table [{tbl}]: (no filter expression)")

finally:
    tom.Disconnect()


# ── Step 2: optionally delete roles ─────────────────────────

if not DELETE_ALL_ROLES and not ROLES_TO_DELETE:
    print("\n" + "=" * 60)
    print("Dry run complete. Review the output above.")
    print("To delete: set DELETE_ALL_ROLES=True, or fill ROLES_TO_DELETE.")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("Deleting roles...")
    print("=" * 60)

    tom = fabric.create_tom_server(readonly=False)
    try:
        db = tom.Databases.GetByName(DATASET_NAME)
        model = db.Model
        deleted = 0
        for r in list(model.Roles):
            if DELETE_ALL_ROLES or r.Name in ROLES_TO_DELETE:
                print(f"  ❌ Removing role: {r.Name}")
                model.Roles.Remove(r)
                deleted += 1
        model.SaveChanges()
        print(f"\n✅ {deleted} role(s) deleted. Try opening the report now.")
    finally:
        tom.Disconnect()
