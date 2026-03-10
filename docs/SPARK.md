# SPARK Integration

SPARK is the IFRC logistics and supply-chain data system. Raw data lives in **Microsoft Fabric** (Azure SQL). The backend pulls it into PostgreSQL, transforms it with **PySpark**, indexes key datasets in **Elasticsearch**, and exposes everything through REST APIs.

```
Fabric (Azure SQL) ─► pull_fabric_data ─► Postgres (Dim/Fct tables)
                                              │
                              PySpark transforms (framework agreements, stock inventory)
                                              │
                                              ▼
                                   CleanedFrameworkAgreement / StockInventory
                                              │
                              bulk_index / create_warehouse_index
                                              │
                                              ▼
                                        Elasticsearch
                                              │
                                              ▼
                                     DRF API endpoints
```

---

## Models

Defined in `api/models.py`.

| Category | Models |
|----------|--------|
| Dimension tables (30) | `DimAgreementLine`, `DimAppeal`, `DimBuyerGroup`, `DimConsignment`, `DimDeliveryMode`, `DimDonor`, `DimInventoryItem`, `DimInventoryItemStatus`, `DimInventoryModule`, `DimInventoryOwner`, `DimInventoryTransaction`, `DimInventoryTransactionLine`, `DimInventoryTransactionOrigin`, `DimItemBatch`, `DimLocation`, `DimLogisticsLocation`, `DimPackingSlipLine`, `DimProduct`, `DimProductCategory`, `DimProductReceiptLine`, `DimProject`, `DimPurchaseOrderLine`, `DimSalesOrderLine`, `DimSite`, `DimVendor`, `DimVendorContact`, `DimVendorContactEmail`, `DimVendorPhysicalAddress`, `DimWarehouse`, `ProductCategoryHierarchyFlattened` |
| Fact tables (4) | `FctAgreement`, `FctProductReceipt`, `FctPurchaseOrder`, `FctSalesOrder` |
| Transformed / cleaned | `CleanedFrameworkAgreement`, `StockInventory` |
| Catalogue | `ItemCodeMapping` (code → URL from Red Cross Item Catalogue) |
| Customs & export AI | `CountryCustomsSnapshot`, `CountryCustomsSource`, `CountryCustomsEvidenceSnippet`, `CountryExportSnapshot`, `CountryExportSource`, `CountryExportEvidenceSnippet` |

---

## Fabric Data Ingestion

| File | Purpose |
|------|---------|
| `api/fabric_sql.py` | Azure SQL connection via pyodbc + Azure CLI credential; token caching |
| `api/fabric_import_map.py` | Maps each Fabric table to its Django model, page key, and pagination strategy |
| `api/management/commands/pull_fabric_data.py` | Management command that pulls all Fabric dimension/fact tables into Postgres in staged, chunked batches |

---

## PySpark Data Transformations

| File | Purpose |
|------|---------|
| `api/data_transformation_framework_agreement.py` | Joins Fabric dimension tables with CSV mappings and GO Admin country/region data to produce `CleanedFrameworkAgreement` rows |
| `api/data_transformation_stock_inventory.py` | Filters and joins inventory transactions, warehouses, products, and item catalogue mappings to produce `StockInventory` rows |
| `api/management/commands/transform_framework_agreement.py` | Django command to run the framework agreement PySpark pipeline |
| `api/management/commands/transform_stock_inventory.py` | Django command to run the stock inventory PySpark pipeline (supports `--dry-run`, `--limit`, warehouse filter, CSV export) |

---

## Elasticsearch Indexes

| File | Purpose |
|------|---------|
| `api/indexes.py` | Defines `warehouse_stocks` and `cleaned_framework_agreements` index names, mappings, and settings |
| `api/management/commands/create_warehouse_index.py` | Creates (or recreates) the `warehouse_stocks` ES index |
| `api/management/commands/bulk_index_warehouse_stocks.py` | Bulk-indexes warehouse stock data from SPARK dimension tables into the `warehouse_stocks` ES index |

---

## API Views and Endpoints

| File | Key views |
|------|-----------|
| `api/drf_views.py` | `CleanedFrameworkAgreementViewSet` (read-only, paginated, ES or DB); `CleanedFrameworkAgreementItemCategoryOptionsView`; `CleanedFrameworkAgreementSummaryView`; `CleanedFrameworkAgreementMapStatsView`; `CustomsRegulationsView` (AI-generated customs updates); `FabricDim*ViewSet` / `FabricFct*ViewSet` for raw Fabric data |
| `api/views.py` | `FabricImportAPIView` — bulk create/truncate of `CleanedFrameworkAgreement` records |
| `api/warehouse_stocks_views.py` | `WarehouseStocksView`, `AggregatedWarehouseStocksView`, `WarehouseStocksSummaryView` — serve warehouse stock data from ES with GO Admin country enrichment |
| `api/warehouse_suggestion_views.py` | `WarehouseSuggestionView` — suggests optimal warehouses by distance scoring and export regulation checks |
| `api/pro_bono_views.py` | `ProBonoServicesView` — serves pro-bono logistics services from `data/ProBono.csv` |

---

## AI Services (Customs & Export Regulations)

| File | Purpose |
|------|---------|
| `api/customs_ai_service.py` | Uses OpenAI web-search to generate per-country customs regulation summaries with evidence snippets and credibility scores |
| `api/export_ai_service.py` | Same approach for export regulations; used by `WarehouseSuggestionView` to check export feasibility |
| `api/customs_data_loader.py` | Loads IFRC customs Q&A data from `data/IFRC_Customs_Data.xlsx` |

---

## Utilities

| File | Purpose |
|------|---------|
| `api/country_distance.py` | Country centroid coordinates + haversine formula for warehouse distance scoring |
| `api/scrapers/item_catalogue.py` | Playwright + requests scraper for the Red Cross Item Catalogue; populates `ItemCodeMapping` |
| `api/management/commands/scrape_items.py` | Management command to run the item catalogue scraper |

---

## Serializers and Filters

| File | Purpose |
|------|---------|
| `api/serializers.py` | `FabricCleanedFrameworkAgreementSerializer` (camelCase), 30+ `FabricDim*Serializer` / `FabricFct*Serializer` classes, `CountryCustomsSnapshotSerializer` and related customs serializers |
| `api/filter_set.py` | `CleanedFrameworkAgreementFilter` — multi-select filtering by region, item category, vendor country |

---

## URL Configuration

All SPARK endpoints are registered in `main/urls.py`:

- `fabric/*` — DRF router for all Dim/Fct ViewSets and `CleanedFrameworkAgreementViewSet`
- `api/v2/fabric/cleaned-framework-agreements/item-categories/` — item category options
- `api/v2/fabric/cleaned-framework-agreements/summary/` — aggregated summary
- `api/v2/fabric/cleaned-framework-agreements/map-stats/` — map statistics
- `api/v2/import/fabric-stage/` — bulk import endpoint
- `api/v1/warehouse-stocks/` — warehouse stock list, aggregated, and summary
- `api/v1/warehouse-suggestions/` — warehouse suggestion endpoint
- `api/v1/pro-bono-services/` — pro-bono services
- `api/v2/country-regulations/` — customs regulation snapshots

---

## Factories and Tests

| File | Purpose |
|------|---------|
| `api/factories/spark.py` | Factory Boy definitions for all SPARK models |
| `api/test_spark_helpers.py` | `SparkTestMixin` — creates a local PySpark session (local mode, 512 MB) for unit tests |
| `api/test_data_transformation_framework_agreement.py` | Tests for framework agreement PySpark pipeline (CSV mapping, country enrichment, join logic) |
| `api/test_data_transformation_stock_inventory.py` | Tests for stock inventory PySpark pipeline (transaction/warehouse/product filters, item catalogue mapping) |
| `api/test_spark_views.py` | Integration tests for warehouse stocks, framework agreement, customs, and pro-bono API endpoints |
| `api/test_models.py` | `SparkModelStrTests` — `__str__` coverage for all SPARK models |

---

## Migrations

| Migration | What it does |
|-----------|-------------|
| `0227` | Creates all SPARK dimension and fact tables |
| `0237` | Creates `CleanedFrameworkAgreements` model |
| `0238` | Renames to `CleanedFrameworkAgreement` |
| `0239` | Adds `owner` and extra fields to `CleanedFrameworkAgreement` |
| `0240` | Creates `CountryCustomsSnapshot`, `CountryCustomsSource`, `CountryCustomsEvidenceSnippet` |
| `0241` | Creates export regulation models |
| `0242` | Alters `CleanedFrameworkAgreement` fields |
| `0243` | Creates `StockInventory` model |
| `0244` | Adds `unit_measurement` to `StockInventory` |
| `0245` | Adds `region` and `catalogue_link` to `StockInventory` |

---

## Data Files

| File | Purpose |
|------|---------|
| `data/ProBono.csv` | Pro-bono logistics services data |
| `data/IFRC_Customs_Data.xlsx` | IFRC customs regulations Q&A by country (not committed — IFRC supplies this file) |

---

## Dependencies

- `pyspark>=3.5.0,<4` — declared in `pyproject.toml`, installed via `uv sync` in Docker
