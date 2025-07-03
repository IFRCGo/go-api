# DREF Utils - Quick Reference

## Import and Basic Usage

```python
from per.dref_temp import dref_manager, DREFFilters

# Get all operations
operations = dref_manager.get_data('final-report')

# Get with filters
filtered = dref_manager.get_data('final-report', DREFFilters(country_name='haiti'))

# Get statistics
stats = dref_manager.get_statistics('final-report')
```

## Data Sources

| Source | Description | Use For |
|--------|-------------|---------|
| `'final-report'` | Completed operations with outcomes | Results, lessons learned, final numbers |
| `'op-update'` | Operations with updates/changes | Tracking modifications, budget changes |
| `'basic'` | Initial applications, active operations | Current ops, planning data |

## Filter Options

```python
filters = DREFFilters(
    # Basic
    id=123,
    title="earthquake",              # Partial match
    appeal_code="MDRHT008",
    
    # Location
    country_name="haiti",            # Partial match
    country_iso="HT",
    region=1,                        # 1=Americas, 2=Asia Pacific, 3=Europe, 4=MENA, 5=Africa
    district_name="ouest",
    
    # Disaster Type
    disaster_type_name="earthquake", # Partial match
    disaster_type_id=1,
    
    # Scale
    min_people_affected=10000,
    max_people_affected=1000000,
    min_budget=100000,
    max_budget=5000000,
    
    # Dates (YYYY-MM-DD format)
    event_date_from="2023-01-01",
    event_date_to="2023-12-31",
    created_from="2023-01-01",
    created_to="2023-12-31",
    
    # Status
    is_published=True,
    emergency_appeal_planned=False,
    
    # Text Search
    search_text="hurricane relief"   # Searches title, description, country, etc.
)
```

## Common Disaster Types

- `"flood"` - Flood operations
- `"earthquake"` - Earthquake operations  
- `"cyclone"` - Cyclone/Hurricane operations
- `"drought"` - Drought operations
- `"population movement"` - Migration/displacement
- `"epidemic"` - Health emergencies
- `"fire"` - Fire disasters
- `"other"` - Other disaster types

## Regions

- `1` - Americas
- `2` - Asia Pacific
- `3` - Europe  
- `4` - MENA (Middle East & North Africa)
- `5` - Africa

## Main Functions

```python
# Load data
operations = dref_manager.get_data(source, filters=None)

# Get statistics
stats = dref_manager.get_statistics(source, filters=None)
# Returns: total_operations, total_people_affected, total_budget, 
#          disaster_types, countries, by_year

# Get unique values
countries = dref_manager.get_unique_countries(source)
disasters = dref_manager.get_unique_disaster_types(source)

# Clear cache (if JSON files updated)
dref_manager.clear_cache()
```

## Quick Examples

```python
# Search by text
hurricane_ops = dref_manager.get_data('final-report', 
    DREFFilters(search_text='hurricane'))

# Large operations in Americas
large_americas = dref_manager.get_data('final-report', 
    DREFFilters(region=1, min_people_affected=50000))

# Recent earthquakes
recent_earthquakes = dref_manager.get_data('basic', 
    DREFFilters(
        disaster_type_name='earthquake',
        event_date_from='2024-01-01'
    ))

# Operations by country
haiti_ops = dref_manager.get_data('final-report', 
    DREFFilters(country_name='haiti'))

# High budget operations
high_budget = dref_manager.get_data('final-report', 
    DREFFilters(min_budget=1000000))
```

## API Response Format

Each operation returns:
```python
{
    'id': 123,
    'title': 'Haiti Earthquake Response',
    'appeal_code': 'MDRHT008',
    'country_details': {
        'name': 'Haiti',
        'iso': 'HT',
        'region': 1
    },
    'disaster_type_details': {
        'id': 1,
        'name': 'Earthquake'
    },
    'number_of_people_affected': 100000,
    'total_dref_allocation': 500000,
    'event_date': '2024-01-15',
    # ... more fields
}
```

## Error Handling

```python
try:
    operations = dref_manager.get_data('final-report')
except FileNotFoundError:
    # JSON files not found
    pass
except Exception as e:
    # Other errors
    pass
```

That's it! All filters support partial matching for text fields.