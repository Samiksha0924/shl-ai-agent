from app.services.catalog_manager import CatalogManager


catalog = CatalogManager()

print("=" * 60)
print(f"Total Assessments : {catalog.total_assessments()}")
print("=" * 60)

first = catalog.get_all()[0]

print(first)

print("=" * 60)

print(catalog.get_by_id(first.entity_id))