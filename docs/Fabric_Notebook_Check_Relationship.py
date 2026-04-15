# Quick check: list all relationships in the model

import sempy.fabric as fabric

DATASET_NAME = "SkillLync-Growth-Master_Report"

tom = fabric.create_tom_server(readonly=True)
try:
    db = tom.Databases.GetByName(DATASET_NAME)
    model = db.Model

    print(f"Relationships in '{DATASET_NAME}':")
    print("-" * 60)

    if model.Relationships.Count == 0:
        print("  (none)")
    else:
        for rel in model.Relationships:
            status = "ACTIVE" if rel.IsActive else "INACTIVE"
            print(f"  {rel.FromTable.Name}[{rel.FromColumn.Name}] → {rel.ToTable.Name}[{rel.ToColumn.Name}]  [{status}]")

    print(f"\nTotal: {model.Relationships.Count}")

    # Also list all tables
    print(f"\nTables in model:")
    for t in model.Tables:
        print(f"  {t.Name} ({t.Columns.Count} cols, {t.Measures.Count} measures)")

finally:
    tom.Disconnect()
