# per/dref_temp/dref_utils.py

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Any, Literal
from datetime import datetime
from collections import defaultdict

from .models import (
    DREFData, DREFFinalReport, DREFOperationalUpdate, DREFBasic,
    CountryDetails, DistrictDetails, DisasterTypeDetails, UserDetails,
    FileDetails, NationalSocietyAction, NeedIdentified, PlannedIntervention,
    RiskSecurity, SourceInformation, Indicator
)

DREFDataSource = Literal['final-report', 'op-update', 'basic']

class DREFFilters:
    """Filter options for DREF data"""
    
    def __init__(self, **kwargs):
        # Basic filters
        self.id: Optional[int] = kwargs.get('id')
        self.title: Optional[str] = kwargs.get('title')
        self.appeal_code: Optional[str] = kwargs.get('appeal_code')
        self.event_date_from: Optional[str] = kwargs.get('event_date_from')
        self.event_date_to: Optional[str] = kwargs.get('event_date_to')
        self.status: Optional[int] = kwargs.get('status')
        
        # Disaster and location filters
        self.disaster_type_id: Optional[int] = kwargs.get('disaster_type_id')
        self.disaster_type_name: Optional[str] = kwargs.get('disaster_type_name')
        self.country_iso: Optional[str] = kwargs.get('country_iso')
        self.country_name: Optional[str] = kwargs.get('country_name')
        self.district_name: Optional[str] = kwargs.get('district_name')
        self.region: Optional[int] = kwargs.get('region')
        
        # Classification filters
        self.type_of_onset: Optional[int] = kwargs.get('type_of_onset')
        self.type_of_dref: Optional[int] = kwargs.get('type_of_dref')
        self.disaster_category: Optional[int] = kwargs.get('disaster_category')
        
        # Scale filters
        self.min_people_affected: Optional[int] = kwargs.get('min_people_affected')
        self.max_people_affected: Optional[int] = kwargs.get('max_people_affected')
        self.min_budget: Optional[int] = kwargs.get('min_budget')
        self.max_budget: Optional[int] = kwargs.get('max_budget')
        
        # Date ranges
        self.created_from: Optional[str] = kwargs.get('created_from')
        self.created_to: Optional[str] = kwargs.get('created_to')
        self.modified_from: Optional[str] = kwargs.get('modified_from')
        self.modified_to: Optional[str] = kwargs.get('modified_to')
        
        # Boolean filters
        self.is_published: Optional[bool] = kwargs.get('is_published')
        self.emergency_appeal_planned: Optional[bool] = kwargs.get('emergency_appeal_planned')
        
        # Text search
        self.search_text: Optional[str] = kwargs.get('search_text')

class DREFManager:
    """Main class for managing DREF data within Django project"""
    
    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            # Use default path relative to this file
            self.data_path = Path(__file__).parent
        else:
            self.data_path = Path(data_path)
        
        self._cache: Dict[DREFDataSource, List[Dict]] = {}
        self._parsed_cache: Dict[DREFDataSource, List[DREFData]] = {}
    
    def _get_filename(self, source: DREFDataSource) -> str:
        """Get filename based on data source"""
        filenames = {
            'final-report': 'dref-final-report.json',
            'op-update': 'dref-op-update.json',
            'basic': 'dref.json'
        }
        return filenames[source]
    
    def _parse_user_details(self, data: Optional[Dict]) -> Optional[UserDetails]:
        """Parse user details from dictionary"""
        if not data:
            return None
        return UserDetails(
            id=data.get('id', 0),
            username=data.get('username', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
    
    def _parse_file_details(self, data: Optional[Dict]) -> Optional[FileDetails]:
        """Parse file details from dictionary"""
        if not data:
            return None
        return FileDetails(
            id=data.get('id', 0),
            file=data.get('file'),
            caption=data.get('caption'),
            created_by=data.get('created_by'),
            client_id=data.get('client_id'),
            translation_module_original_language=data.get('translation_module_original_language', 'en'),
            translation_module_skip_auto_translation=data.get('translation_module_skip_auto_translation', False),
            created_by_details=self._parse_user_details(data.get('created_by_details'))
        )
    
    def _parse_country_details(self, data: Dict) -> CountryDetails:
        """Parse country details from dictionary"""
        return CountryDetails(
            iso=data.get('iso', ''),
            iso3=data.get('iso3', ''),
            id=data.get('id', 0),
            name=data.get('name', ''),
            society_name=data.get('society_name', ''),
            region=data.get('region', 0),
            independent=data.get('independent', True),
            record_type=data.get('record_type', 1),
            record_type_display=data.get('record_type_display', 'Country'),
            is_deprecated=data.get('is_deprecated', False),
            fdrs=data.get('fdrs', ''),
            average_household_size=data.get('average_household_size'),
            translation_module_original_language=data.get('translation_module_original_language', 'en')
        )
    
    def _parse_district_details(self, data: List[Dict]) -> List[DistrictDetails]:
        """Parse district details from list of dictionaries"""
        return [
            DistrictDetails(
                name=item.get('name', ''),
                code=item.get('code', ''),
                id=item.get('id', 0),
                is_enclave=item.get('is_enclave', False),
                is_deprecated=item.get('is_deprecated', False)
            )
            for item in data
        ]
    
    def _parse_disaster_type_details(self, data: Dict) -> DisasterTypeDetails:
        """Parse disaster type details from dictionary"""
        return DisasterTypeDetails(
            id=data.get('id', 0),
            name=data.get('name', ''),
            summary=data.get('summary', ''),
            translation_module_original_language=data.get('translation_module_original_language', 'en')
        )
    
    def _parse_base_dref(self, data: Dict) -> Dict:
        """Parse base DREF properties"""
        return {
            'id': data.get('id', 0),
            'title': data.get('title', ''),
            'appeal_code': data.get('appeal_code', ''),
            'glide_code': data.get('glide_code'),
            'event_date': data.get('event_date', ''),
            'ns_respond_date': data.get('ns_respond_date', ''),
            'created_at': data.get('created_at', ''),
            'modified_at': data.get('modified_at', ''),
            'type_of_onset': data.get('type_of_onset', 0),
            'type_of_onset_display': data.get('type_of_onset_display', ''),
            'type_of_dref': data.get('type_of_dref', 0),
            'type_of_dref_display': data.get('type_of_dref_display', ''),
            'disaster_category': data.get('disaster_category', 0),
            'disaster_category_display': data.get('disaster_category_display', ''),
            'status': data.get('status', 0),
            'country_details': self._parse_country_details(data.get('country_details', {})),
            'district_details': self._parse_district_details(data.get('district_details', [])),
            'disaster_type_details': self._parse_disaster_type_details(data.get('disaster_type_details', {})),
            'number_of_people_affected': data.get('number_of_people_affected', 0),
            'total_targeted_population': data.get('total_targeted_population', 0),
            'women': data.get('women', 0),
            'men': data.get('men', 0),
            'girls': data.get('girls', 0),
            'boys': data.get('boys', 0),
            'disability_people_per': data.get('disability_people_per', 0.0),
            'total_dref_allocation': data.get('total_dref_allocation'),
            'amount_requested': data.get('amount_requested'),
            'operation_start_date': data.get('operation_start_date'),
            'operation_end_date': data.get('operation_end_date'),
            'total_operation_timeframe': data.get('total_operation_timeframe'),
            'ifrc_appeal_manager_name': data.get('ifrc_appeal_manager_name', ''),
            'ifrc_appeal_manager_email': data.get('ifrc_appeal_manager_email', ''),
            'ifrc_appeal_manager_title': data.get('ifrc_appeal_manager_title', ''),
            'ifrc_project_manager_name': data.get('ifrc_project_manager_name', ''),
            'ifrc_project_manager_email': data.get('ifrc_project_manager_email', ''),
            'ifrc_project_manager_title': data.get('ifrc_project_manager_title', ''),
            'national_society_contact_name': data.get('national_society_contact_name', ''),
            'national_society_contact_email': data.get('national_society_contact_email', ''),
            'national_society_contact_title': data.get('national_society_contact_title', ''),
            'national_society_actions': [],  # Simplified for Django integration
            'needs_identified': [],
            'planned_interventions': [],
            'risk_security': [],
            'source_information': [],
            'event_map_file': self._parse_file_details(data.get('event_map_file')),
            'cover_image_file': self._parse_file_details(data.get('cover_image_file')),
            'images_file': [],
            'created_by_details': self._parse_user_details(data.get('created_by_details')),
            'modified_by_details': self._parse_user_details(data.get('modified_by_details')),
            'users_details': [],
            'is_published': data.get('is_published', True),
            'translation_module_original_language': data.get('translation_module_original_language', 'en'),
            'translation_module_skip_auto_translation': data.get('translation_module_skip_auto_translation', False)
        }
    
    def _parse_dref_data(self, data: Dict, source: DREFDataSource) -> DREFData:
        """Parse DREF data based on source type"""
        base_data = self._parse_base_dref(data)
        
        if source == 'final-report':
            return DREFFinalReport(
                **base_data,
                financial_report_details=self._parse_file_details(data.get('financial_report_details')),
                financial_report_preview=data.get('financial_report_preview'),
                financial_report_description=data.get('financial_report_description'),
                num_assisted=data.get('num_assisted'),
                assisted_num_of_women=data.get('assisted_num_of_women'),
                assisted_num_of_men=data.get('assisted_num_of_men'),
                main_donors=data.get('main_donors'),
                operation_objective=data.get('operation_objective'),
                selection_criteria=data.get('selection_criteria'),
                national_authorities=data.get('national_authorities'),
                partner_national_society=data.get('partner_national_society'),
                icrc=data.get('icrc'),
                ifrc=data.get('ifrc'),
                event_description=data.get('event_description'),
                event_scope=data.get('event_scope'),
                response_strategy=data.get('response_strategy'),
                people_assisted=data.get('people_assisted'),
                change_in_operational_strategy=data.get('change_in_operational_strategy'),
                change_in_operational_strategy_text=data.get('change_in_operational_strategy_text')
            )
        elif source == 'op-update':
            return DREFOperationalUpdate(
                **base_data,
                operational_update_number=data.get('operational_update_number'),
                budget_file_details=self._parse_file_details(data.get('budget_file_details')),
                budget_file_preview=data.get('budget_file_preview'),
                dref_allocated_so_far=data.get('dref_allocated_so_far'),
                additional_allocation=data.get('additional_allocation'),
                emergency_appeal_planned=data.get('emergency_appeal_planned'),
                summary_of_change=data.get('summary_of_change'),
                event_scope=data.get('event_scope'),
                event_description=data.get('event_description'),
                national_authorities=data.get('national_authorities'),
                response_strategy=data.get('response_strategy')
            )
        else:  # basic
            return DREFBasic(
                **base_data,
                budget_file_details=self._parse_file_details(data.get('budget_file_details')),
                budget_file_preview=data.get('budget_file_preview'),
                assessment_report_details=self._parse_file_details(data.get('assessment_report_details')),
                end_date=data.get('end_date'),
                publishing_date=data.get('publishing_date'),
                operation_timeframe=data.get('operation_timeframe'),
                submission_to_geneva=data.get('submission_to_geneva'),
                date_of_approval=data.get('date_of_approval'),
                ns_request_date=data.get('ns_request_date'),
                people_in_need=data.get('people_in_need'),
                government_requested_assistance=data.get('government_requested_assistance'),
                event_scope=data.get('event_scope'),
                event_description=data.get('event_description'),
                operation_objective=data.get('operation_objective'),
                national_authorities=data.get('national_authorities')
            )
    
    def load_data(self, source: DREFDataSource) -> List[DREFData]:
        """Load data from specified JSON file"""
        if source in self._parsed_cache:
            return self._parsed_cache[source]
        
        if source not in self._cache:
            filename = self._get_filename(source)
            file_path = self.data_path / filename
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    self._cache[source] = raw_data
            except FileNotFoundError:
                raise FileNotFoundError(f"DREF data file not found: {file_path}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in DREF file {filename}: {e}")
        
        # Parse raw data
        raw_data = self._cache[source]
        parsed_data = []
        
        for item in raw_data:
            try:
                parsed_item = self._parse_dref_data(item, source)
                parsed_data.append(parsed_item)
            except Exception:
                # Skip invalid records silently for Django integration
                continue
        
        self._parsed_cache[source] = parsed_data
        return parsed_data
    
    def filter_data(self, data: List[DREFData], filters: DREFFilters) -> List[DREFData]:
        """Filter data based on provided criteria"""
        filtered_data = []
        
        for item in data:
            # Apply filters
            if filters.id and item.id != filters.id:
                continue
            if filters.title and filters.title.lower() not in item.title.lower():
                continue
            if filters.appeal_code and item.appeal_code != filters.appeal_code:
                continue
            if filters.event_date_from and item.event_date < filters.event_date_from:
                continue
            if filters.event_date_to and item.event_date > filters.event_date_to:
                continue
            if filters.status and item.status != filters.status:
                continue
            if filters.disaster_type_id and item.disaster_type_details.id != filters.disaster_type_id:
                continue
            if (filters.disaster_type_name and 
                filters.disaster_type_name.lower() not in item.disaster_type_details.name.lower()):
                continue
            if filters.country_iso and item.country_details.iso != filters.country_iso:
                continue
            if (filters.country_name and 
                filters.country_name.lower() not in item.country_details.name.lower()):
                continue
            if filters.district_name:
                district_match = any(
                    filters.district_name.lower() in d.name.lower() 
                    for d in item.district_details
                )
                if not district_match:
                    continue
            if filters.region and item.country_details.region != filters.region:
                continue
            if filters.type_of_onset and item.type_of_onset != filters.type_of_onset:
                continue
            if filters.type_of_dref and item.type_of_dref != filters.type_of_dref:
                continue
            if filters.disaster_category and item.disaster_category != filters.disaster_category:
                continue
            if (filters.min_people_affected and 
                item.number_of_people_affected < filters.min_people_affected):
                continue
            if (filters.max_people_affected and 
                item.number_of_people_affected > filters.max_people_affected):
                continue
            
            # Budget filters
            budget = item.total_dref_allocation or getattr(item, 'amount_requested', 0) or 0
            if filters.min_budget and budget < filters.min_budget:
                continue
            if filters.max_budget and budget > filters.max_budget:
                continue
            
            # Date range filters
            if filters.created_from and item.created_at < filters.created_from:
                continue
            if filters.created_to and item.created_at > filters.created_to:
                continue
            if filters.modified_from and item.modified_at < filters.modified_from:
                continue
            if filters.modified_to and item.modified_at > filters.modified_to:
                continue
            
            # Boolean filters
            if filters.is_published is not None and item.is_published != filters.is_published:
                continue
            if (filters.emergency_appeal_planned is not None and 
                getattr(item, 'emergency_appeal_planned', None) != filters.emergency_appeal_planned):
                continue
            
            # Text search
            if filters.search_text:
                search_text = filters.search_text.lower()
                search_fields = [
                    item.title,
                    getattr(item, 'event_description', '') or '',
                    getattr(item, 'event_scope', '') or '',
                    item.disaster_type_details.name,
                    item.country_details.name,
                    item.country_details.society_name
                ]
                
                if not any(field and search_text in field.lower() for field in search_fields):
                    continue
            
            filtered_data.append(item)
        
        return filtered_data
    
    def get_data(self, source: DREFDataSource, filters: Optional[DREFFilters] = None) -> List[DREFData]:
        """Get data with optional filters applied"""
        data = self.load_data(source)
        
        if not filters:
            return data
        
        return self.filter_data(data, filters)
    
    def get_statistics(self, source: DREFDataSource, filters: Optional[DREFFilters] = None) -> Dict[str, Any]:
        """Get statistics for a dataset"""
        data = self.get_data(source, filters)
        
        stats = {
            'total_operations': len(data),
            'total_people_affected': 0,
            'total_budget': 0,
            'avg_people_affected': 0,
            'avg_budget': 0,
            'disaster_types': defaultdict(int),
            'countries': defaultdict(int),
            'by_year': defaultdict(int)
        }
        
        for item in data:
            stats['total_people_affected'] += item.number_of_people_affected or 0
            
            budget = item.total_dref_allocation or getattr(item, 'amount_requested', 0) or 0
            stats['total_budget'] += budget
            
            stats['disaster_types'][item.disaster_type_details.name] += 1
            stats['countries'][item.country_details.name] += 1
            
            try:
                year = datetime.fromisoformat(item.event_date.replace('Z', '+00:00')).year
                stats['by_year'][str(year)] += 1
            except (ValueError, AttributeError):
                pass
        
        # Calculate averages
        if len(data) > 0:
            stats['avg_people_affected'] = stats['total_people_affected'] / len(data)
            stats['avg_budget'] = stats['total_budget'] / len(data)
        
        # Convert defaultdicts to regular dicts
        stats['disaster_types'] = dict(stats['disaster_types'])
        stats['countries'] = dict(stats['countries'])
        stats['by_year'] = dict(stats['by_year'])
        
        return stats
    
    def get_unique_disaster_types(self, source: DREFDataSource) -> List[DisasterTypeDetails]:
        """Get unique disaster types from data"""
        data = self.load_data(source)
        unique_types = {}
        
        for item in data:
            disaster_type = item.disaster_type_details
            if disaster_type.id not in unique_types:
                unique_types[disaster_type.id] = disaster_type
        
        return list(unique_types.values())
    
    def get_unique_countries(self, source: DREFDataSource) -> List[CountryDetails]:
        """Get unique countries from data"""
        data = self.load_data(source)
        unique_countries = {}
        
        for item in data:
            country = item.country_details
            if country.id not in unique_countries:
                unique_countries[country.id] = country
        
        return list(unique_countries.values())
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        self._parsed_cache.clear()

# Create a default instance for easy importing
dref_manager = DREFManager()