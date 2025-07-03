# per/dref_temp/examples.py

"""
Examples of how to use DREF utilities in Django views and other parts of the project
"""

from .dref_utils import dref_manager, DREFFilters
from .models import DREFData

# Example 1: Basic usage in Django views
def get_dref_operations_view_example():
    """Example for use in drf_views.py"""
    
    # Load all final report operations
    operations = dref_manager.get_data('final-report')
    
    # Convert to simple dict format for API response
    operations_data = []
    for op in operations:
        operations_data.append({
            'id': op.id,
            'title': op.title,
            'appeal_code': op.appeal_code,
            'country': op.country_details.name,
            'disaster_type': op.disaster_type_details.name,
            'people_affected': op.number_of_people_affected,
            'event_date': op.event_date,
            'budget': op.total_dref_allocation
        })
    
    return operations_data

# Example 2: Filtered data for API endpoints
def get_filtered_operations(country=None, disaster_type=None, year=None):
    """Example of filtering for API responses"""
    
    filters = DREFFilters()
    
    if country:
        filters.country_name = country
    if disaster_type:
        filters.disaster_type_name = disaster_type
    if year:
        filters.event_date_from = f"{year}-01-01"
        filters.event_date_to = f"{year}-12-31"
    
    operations = dref_manager.get_data('final-report', filters)
    
    return [{
        'id': op.id,
        'title': op.title,
        'appeal_code': op.appeal_code,
        'country': op.country_details.name,
        'disaster_type': op.disaster_type_details.name,
        'people_affected': op.number_of_people_affected,
        'event_date': op.event_date,
        'budget': op.total_dref_allocation
    } for op in operations]

# Example 3: Statistics for dashboard
def get_dref_statistics():
    """Example for dashboard statistics"""
    
    stats = dref_manager.get_statistics('final-report')
    
    return {
        'total_operations': stats['total_operations'],
        'total_people_affected': stats['total_people_affected'],
        'total_budget': stats['total_budget'],
        'avg_people_affected': int(stats['avg_people_affected']),
        'avg_budget': int(stats['avg_budget']),
        'top_disaster_types': dict(sorted(
            stats['disaster_types'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]),
        'top_countries': dict(sorted(
            stats['countries'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]),
        'operations_by_year': stats['by_year']
    }

# Example 4: Search functionality
def search_operations(query):
    """Example search function"""
    
    filters = DREFFilters(search_text=query)
    operations = dref_manager.get_data('final-report', filters)
    
    return [{
        'id': op.id,
        'title': op.title,
        'appeal_code': op.appeal_code,
        'country': op.country_details.name,
        'disaster_type': op.disaster_type_details.name,
        'relevance_score': 1.0  # You could implement actual relevance scoring
    } for op in operations]

# Example 5: Country-specific operations
def get_operations_by_country(country_iso):
    """Get operations for a specific country"""
    
    filters = DREFFilters(country_iso=country_iso)
    operations = dref_manager.get_data('final-report', filters)
    
    return operations

# Example 6: Recent operations
def get_recent_operations(days=30):
    """Get recent operations"""
    from datetime import datetime, timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    filters = DREFFilters(created_from=cutoff_date)
    
    operations = dref_manager.get_data('basic', filters)
    
    return operations

# Example 7: Large scale operations
def get_large_scale_operations(min_people=50000):
    """Get large scale operations"""
    
    filters = DREFFilters(min_people_affected=min_people)
    operations = dref_manager.get_data('final-report', filters)
    
    return operations

# Example 8: Operations by disaster type
def get_operations_by_disaster_type(disaster_type):
    """Get operations by disaster type"""
    
    filters = DREFFilters(disaster_type_name=disaster_type)
    operations = dref_manager.get_data('final-report', filters)
    
    return operations

# Example 9: Available options for dropdowns/filters
def get_filter_options():
    """Get available options for UI filters"""
    
    disaster_types = dref_manager.get_unique_disaster_types('final-report')
    countries = dref_manager.get_unique_countries('final-report')
    
    return {
        'disaster_types': [{'id': dt.id, 'name': dt.name} for dt in disaster_types],
        'countries': [{'id': c.id, 'name': c.name, 'iso': c.iso} for c in countries],
        'regions': [
            {'id': 1, 'name': 'Americas'},
            {'id': 2, 'name': 'Asia Pacific'},
            {'id': 3, 'name': 'Europe'},
            {'id': 4, 'name': 'MENA'},
            {'id': 5, 'name': 'Africa'}
        ]
    }

# Example 10: Complex filtering for advanced search
def advanced_search(country=None, disaster_type=None, min_budget=None, 
                   max_budget=None, date_from=None, date_to=None):
    """Advanced search with multiple filters"""
    
    filters = DREFFilters(
        country_name=country,
        disaster_type_name=disaster_type,
        min_budget=min_budget,
        max_budget=max_budget,
        event_date_from=date_from,
        event_date_to=date_to
    )
    
    operations = dref_manager.get_data('final-report', filters)
    
    return operations