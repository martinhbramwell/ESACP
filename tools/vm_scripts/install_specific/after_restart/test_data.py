"""Idempotent test records: Customer, Item, Address, Invoice."""

from urllib.error import HTTPError, URLError
from urllib.parse import quote as urlquote

from .._http import api_get, api_post


def _create_test_records(rsrc_url, api_key, datasets):
    """GET-then-POST each record; skip if it already exists."""
    for doc_type, doc_name, record in datasets:
        post_url = f"{rsrc_url}/{urlquote(doc_type)}"
        get_url = f"{post_url}/{urlquote(doc_name)}"
        try:
            resp = api_get(get_url, api_key)
            if "exc_type" in resp and resp["exc_type"] == "DoesNotExistError":
                raise URLError("not found")
            print(f"  [OK] {doc_type} '{resp['data']['name']}' exists")
        except (URLError, HTTPError, KeyError):
            resp = api_post(post_url, api_key, record)
            print(f"  [OK] Created {doc_type} '{resp['data']['name']}'")


def install_test_data(rsrc_url, api_key, test_suc_pde):
    datasets = [
        ("Item Group", "Grupo de Prueba", {
            "parent": "Todos los Grupos de Artículos",
            "item_group_name": "Grupo de Prueba",
            "parent_item_group": "Todos los Grupos de Artículos",
        }),
        ("Customer Group", "Grupo de Prueba", {
            "parent_customer_group": "Todas las categorías de clientes",
            "customer_group_name": "Grupo de Prueba",
        }),
        ("Item", "Item de Prueba", {
            "item_code": "Item de Prueba",
            "item_group": "Grupo de Prueba",
        }),
        ("Customer", "Cliente de Prueba", {
            "customer_name": "Cliente de Prueba",
            "tax_id": "1793141528001",
            "customer_details": "id_bapu = '0'",
            "territory": "Ecuador",
            "customer_group": "Grupo de Prueba",
        }),
        ("Address", "Cliente de Prueba-Postal", {
            "address_line1": "10123 Avenida de Pruebas",
            "city": "Pruebaburgo",
            "email_id": "prueba.cliente@hotmail.com",
            "phone": "2376543",
            "address_type": "Postal",
            "links": [{"link_doctype": "Customer", "link_name": "Cliente de Prueba"}],
        }),
        ("Sales Invoice", f"{test_suc_pde}-000000000", {
            "naming_series": f"{test_suc_pde}-.#########",
            "customer": "Cliente de Prueba",
            "tax_id": "1793141528001",
            "due_date": "2028-05-24",
            "items": [{"item_code": "Item de Prueba", "qty": 1, "rate": 1}],
        }),
    ]
    _create_test_records(rsrc_url, api_key, datasets)
