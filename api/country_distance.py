"""
Country distance calculations using centroid coordinates and haversine formula.
Used for warehouse suggestion scoring.
"""

import logging
import math
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# Country centroids (latitude, longitude) by ISO3 code
# Data sourced from average geometric centers of countries
COUNTRY_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "AFG": (33.9391, 67.7100),  # Afghanistan
    "ALB": (41.1533, 20.1683),  # Albania
    "DZA": (28.0339, 1.6596),  # Algeria
    "AND": (42.5063, 1.5218),  # Andorra
    "AGO": (-11.2027, 17.8739),  # Angola
    "ATG": (17.0608, -61.7964),  # Antigua and Barbuda
    "ARG": (-38.4161, -63.6167),  # Argentina
    "ARM": (40.0691, 45.0382),  # Armenia
    "AUS": (-25.2744, 133.7751),  # Australia
    "AUT": (47.5162, 14.5501),  # Austria
    "AZE": (40.1431, 47.5769),  # Azerbaijan
    "BHS": (25.0343, -77.3963),  # Bahamas
    "BHR": (26.0667, 50.5577),  # Bahrain
    "BGD": (23.6850, 90.3563),  # Bangladesh
    "BRB": (13.1939, -59.5432),  # Barbados
    "BLR": (53.7098, 27.9534),  # Belarus
    "BEL": (50.5039, 4.4699),  # Belgium
    "BLZ": (17.1899, -88.4976),  # Belize
    "BEN": (9.3077, 2.3158),  # Benin
    "BTN": (27.5142, 90.4336),  # Bhutan
    "BOL": (-16.2902, -63.5887),  # Bolivia
    "BIH": (43.9159, 17.6791),  # Bosnia and Herzegovina
    "BWA": (-22.3285, 24.6849),  # Botswana
    "BRA": (-14.2350, -51.9253),  # Brazil
    "BRN": (4.5353, 114.7277),  # Brunei
    "BGR": (42.7339, 25.4858),  # Bulgaria
    "BFA": (12.2383, -1.5616),  # Burkina Faso
    "BDI": (-3.3731, 29.9189),  # Burundi
    "KHM": (12.5657, 104.9910),  # Cambodia
    "CMR": (7.3697, 12.3547),  # Cameroon
    "CAN": (56.1304, -106.3468),  # Canada
    "CPV": (16.5388, -23.0418),  # Cape Verde
    "CAF": (6.6111, 20.9394),  # Central African Republic
    "TCD": (15.4542, 18.7322),  # Chad
    "CHL": (-35.6751, -71.5430),  # Chile
    "CHN": (35.8617, 104.1954),  # China
    "COL": (4.5709, -74.2973),  # Colombia
    "COM": (-11.6455, 43.3333),  # Comoros
    "COG": (-0.2280, 15.8277),  # Congo
    "COD": (-4.0383, 21.7587),  # DR Congo
    "CRI": (9.7489, -83.7534),  # Costa Rica
    "CIV": (7.5400, -5.5471),  # Côte d'Ivoire
    "HRV": (45.1000, 15.2000),  # Croatia
    "CUB": (21.5218, -77.7812),  # Cuba
    "CYP": (35.1264, 33.4299),  # Cyprus
    "CZE": (49.8175, 15.4730),  # Czech Republic
    "DNK": (56.2639, 9.5018),  # Denmark
    "DJI": (11.8251, 42.5903),  # Djibouti
    "DMA": (15.4150, -61.3710),  # Dominica
    "DOM": (18.7357, -70.1627),  # Dominican Republic
    "ECU": (-1.8312, -78.1834),  # Ecuador
    "EGY": (26.8206, 30.8025),  # Egypt
    "SLV": (13.7942, -88.8965),  # El Salvador
    "GNQ": (1.6508, 10.2679),  # Equatorial Guinea
    "ERI": (15.1794, 39.7823),  # Eritrea
    "EST": (58.5953, 25.0136),  # Estonia
    "SWZ": (-26.5225, 31.4659),  # Eswatini
    "ETH": (9.1450, 40.4897),  # Ethiopia
    "FJI": (-17.7134, 178.0650),  # Fiji
    "FIN": (61.9241, 25.7482),  # Finland
    "FRA": (46.2276, 2.2137),  # France
    "GAB": (-0.8037, 11.6094),  # Gabon
    "GMB": (13.4432, -15.3101),  # Gambia
    "GEO": (42.3154, 43.3569),  # Georgia
    "DEU": (51.1657, 10.4515),  # Germany
    "GHA": (7.9465, -1.0232),  # Ghana
    "GRC": (39.0742, 21.8243),  # Greece
    "GRD": (12.1165, -61.6790),  # Grenada
    "GTM": (15.7835, -90.2308),  # Guatemala
    "GIN": (9.9456, -9.6966),  # Guinea
    "GNB": (11.8037, -15.1804),  # Guinea-Bissau
    "GUY": (4.8604, -58.9302),  # Guyana
    "HTI": (18.9712, -72.2852),  # Haiti
    "HND": (15.2000, -86.2419),  # Honduras
    "HUN": (47.1625, 19.5033),  # Hungary
    "ISL": (64.9631, -19.0208),  # Iceland
    "IND": (20.5937, 78.9629),  # India
    "IDN": (-0.7893, 113.9213),  # Indonesia
    "IRN": (32.4279, 53.6880),  # Iran
    "IRQ": (33.2232, 43.6793),  # Iraq
    "IRL": (53.1424, -7.6921),  # Ireland
    "ISR": (31.0461, 34.8516),  # Israel
    "ITA": (41.8719, 12.5674),  # Italy
    "JAM": (18.1096, -77.2975),  # Jamaica
    "JPN": (36.2048, 138.2529),  # Japan
    "JOR": (30.5852, 36.2384),  # Jordan
    "KAZ": (48.0196, 66.9237),  # Kazakhstan
    "KEN": (-0.0236, 37.9062),  # Kenya
    "KIR": (-3.3704, -168.7340),  # Kiribati
    "PRK": (40.3399, 127.5101),  # North Korea
    "KOR": (35.9078, 127.7669),  # South Korea
    "KWT": (29.3117, 47.4818),  # Kuwait
    "KGZ": (41.2044, 74.7661),  # Kyrgyzstan
    "LAO": (19.8563, 102.4955),  # Laos
    "LVA": (56.8796, 24.6032),  # Latvia
    "LBN": (33.8547, 35.8623),  # Lebanon
    "LSO": (-29.6100, 28.2336),  # Lesotho
    "LBR": (6.4281, -9.4295),  # Liberia
    "LBY": (26.3351, 17.2283),  # Libya
    "LIE": (47.1660, 9.5554),  # Liechtenstein
    "LTU": (55.1694, 23.8813),  # Lithuania
    "LUX": (49.8153, 6.1296),  # Luxembourg
    "MDG": (-18.7669, 46.8691),  # Madagascar
    "MWI": (-13.2543, 34.3015),  # Malawi
    "MYS": (4.2105, 101.9758),  # Malaysia
    "MDV": (3.2028, 73.2207),  # Maldives
    "MLI": (17.5707, -3.9962),  # Mali
    "MLT": (35.9375, 14.3754),  # Malta
    "MHL": (7.1315, 171.1845),  # Marshall Islands
    "MRT": (21.0079, -10.9408),  # Mauritania
    "MUS": (-20.3484, 57.5522),  # Mauritius
    "MEX": (23.6345, -102.5528),  # Mexico
    "FSM": (7.4256, 150.5508),  # Micronesia
    "MDA": (47.4116, 28.3699),  # Moldova
    "MCO": (43.7384, 7.4246),  # Monaco
    "MNG": (46.8625, 103.8467),  # Mongolia
    "MNE": (42.7087, 19.3744),  # Montenegro
    "MAR": (31.7917, -7.0926),  # Morocco
    "MOZ": (-18.6657, 35.5296),  # Mozambique
    "MMR": (21.9162, 95.9560),  # Myanmar
    "NAM": (-22.9576, 18.4904),  # Namibia
    "NRU": (-0.5228, 166.9315),  # Nauru
    "NPL": (28.3949, 84.1240),  # Nepal
    "NLD": (52.1326, 5.2913),  # Netherlands
    "NZL": (-40.9006, 174.8860),  # New Zealand
    "NIC": (12.8654, -85.2072),  # Nicaragua
    "NER": (17.6078, 8.0817),  # Niger
    "NGA": (9.0820, 8.6753),  # Nigeria
    "MKD": (41.5124, 21.7453),  # North Macedonia
    "NOR": (60.4720, 8.4689),  # Norway
    "OMN": (21.4735, 55.9754),  # Oman
    "PAK": (30.3753, 69.3451),  # Pakistan
    "PLW": (7.5150, 134.5825),  # Palau
    "PSE": (31.9522, 35.2332),  # Palestine
    "PAN": (8.5380, -80.7821),  # Panama
    "PNG": (-6.3150, 143.9555),  # Papua New Guinea
    "PRY": (-23.4425, -58.4438),  # Paraguay
    "PER": (-9.1900, -75.0152),  # Peru
    "PHL": (12.8797, 121.7740),  # Philippines
    "POL": (51.9194, 19.1451),  # Poland
    "PRT": (39.3999, -8.2245),  # Portugal
    "QAT": (25.3548, 51.1839),  # Qatar
    "ROU": (45.9432, 24.9668),  # Romania
    "RUS": (61.5240, 105.3188),  # Russia
    "RWA": (-1.9403, 29.8739),  # Rwanda
    "KNA": (17.3578, -62.7830),  # Saint Kitts and Nevis
    "LCA": (13.9094, -60.9789),  # Saint Lucia
    "VCT": (12.9843, -61.2872),  # Saint Vincent
    "WSM": (-13.7590, -172.1046),  # Samoa
    "SMR": (43.9424, 12.4578),  # San Marino
    "STP": (0.1864, 6.6131),  # São Tomé and Príncipe
    "SAU": (23.8859, 45.0792),  # Saudi Arabia
    "SEN": (14.4974, -14.4524),  # Senegal
    "SRB": (44.0165, 21.0059),  # Serbia
    "SYC": (-4.6796, 55.4920),  # Seychelles
    "SLE": (8.4606, -11.7799),  # Sierra Leone
    "SGP": (1.3521, 103.8198),  # Singapore
    "SVK": (48.6690, 19.6990),  # Slovakia
    "SVN": (46.1512, 14.9955),  # Slovenia
    "SLB": (-9.6457, 160.1562),  # Solomon Islands
    "SOM": (5.1521, 46.1996),  # Somalia
    "ZAF": (-30.5595, 22.9375),  # South Africa
    "SSD": (6.8770, 31.3070),  # South Sudan
    "ESP": (40.4637, -3.7492),  # Spain
    "LKA": (7.8731, 80.7718),  # Sri Lanka
    "SDN": (12.8628, 30.2176),  # Sudan
    "SUR": (3.9193, -56.0278),  # Suriname
    "SWE": (60.1282, 18.6435),  # Sweden
    "CHE": (46.8182, 8.2275),  # Switzerland
    "SYR": (34.8021, 38.9968),  # Syria
    "TWN": (23.6978, 120.9605),  # Taiwan
    "TJK": (38.8610, 71.2761),  # Tajikistan
    "TZA": (-6.3690, 34.8888),  # Tanzania
    "THA": (15.8700, 100.9925),  # Thailand
    "TLS": (-8.8742, 125.7275),  # Timor-Leste
    "TGO": (8.6195, 0.8248),  # Togo
    "TON": (-21.1790, -175.1982),  # Tonga
    "TTO": (10.6918, -61.2225),  # Trinidad and Tobago
    "TUN": (33.8869, 9.5375),  # Tunisia
    "TUR": (38.9637, 35.2433),  # Turkey
    "TKM": (38.9697, 59.5563),  # Turkmenistan
    "TUV": (-7.1095, 177.6493),  # Tuvalu
    "UGA": (1.3733, 32.2903),  # Uganda
    "UKR": (48.3794, 31.1656),  # Ukraine
    "ARE": (23.4241, 53.8478),  # United Arab Emirates
    "GBR": (55.3781, -3.4360),  # United Kingdom
    "USA": (37.0902, -95.7129),  # United States
    "URY": (-32.5228, -55.7658),  # Uruguay
    "UZB": (41.3775, 64.5853),  # Uzbekistan
    "VUT": (-15.3767, 166.9592),  # Vanuatu
    "VAT": (41.9029, 12.4534),  # Vatican City
    "VEN": (6.4238, -66.5897),  # Venezuela
    "VNM": (14.0583, 108.2772),  # Vietnam
    "YEM": (15.5527, 48.5164),  # Yemen
    "ZMB": (-13.1339, 27.8493),  # Zambia
    "ZWE": (-19.0154, 29.1549),  # Zimbabwe
    # Additional territories
    "HKG": (22.3193, 114.1694),  # Hong Kong
    "MAC": (22.1987, 113.5439),  # Macau
    "PRI": (18.2208, -66.5901),  # Puerto Rico
    "GUM": (13.4443, 144.7937),  # Guam
    "VIR": (18.3358, -64.8963),  # US Virgin Islands
    "ASM": (-14.2710, -170.1322),  # American Samoa
    "GLP": (16.2650, -61.5510),  # Guadeloupe
    "MTQ": (14.6415, -61.0242),  # Martinique
    "REU": (-21.1151, 55.5364),  # Réunion
    "GUF": (3.9339, -53.1258),  # French Guiana
    "NCL": (-20.9043, 165.6180),  # New Caledonia
    "PYF": (-17.6797, -149.4068),  # French Polynesia
    "XKX": (42.6026, 20.9030),  # Kosovo
}

# Alternative name mappings to ISO3
COUNTRY_NAME_TO_ISO3: Dict[str, str] = {
    "afghanistan": "AFG",
    "albania": "ALB",
    "algeria": "DZA",
    "andorra": "AND",
    "angola": "AGO",
    "antigua and barbuda": "ATG",
    "argentina": "ARG",
    "armenia": "ARM",
    "australia": "AUS",
    "austria": "AUT",
    "azerbaijan": "AZE",
    "bahamas": "BHS",
    "bahrain": "BHR",
    "bangladesh": "BGD",
    "barbados": "BRB",
    "belarus": "BLR",
    "belgium": "BEL",
    "belize": "BLZ",
    "benin": "BEN",
    "bhutan": "BTN",
    "bolivia": "BOL",
    "bosnia and herzegovina": "BIH",
    "bosnia": "BIH",
    "botswana": "BWA",
    "brazil": "BRA",
    "brunei": "BRN",
    "bulgaria": "BGR",
    "burkina faso": "BFA",
    "burundi": "BDI",
    "cambodia": "KHM",
    "cameroon": "CMR",
    "canada": "CAN",
    "cape verde": "CPV",
    "cabo verde": "CPV",
    "central african republic": "CAF",
    "chad": "TCD",
    "chile": "CHL",
    "china": "CHN",
    "colombia": "COL",
    "comoros": "COM",
    "congo": "COG",
    "republic of the congo": "COG",
    "democratic republic of the congo": "COD",
    "dr congo": "COD",
    "drc": "COD",
    "costa rica": "CRI",
    "cote d'ivoire": "CIV",
    "ivory coast": "CIV",
    "croatia": "HRV",
    "cuba": "CUB",
    "cyprus": "CYP",
    "czech republic": "CZE",
    "czechia": "CZE",
    "denmark": "DNK",
    "djibouti": "DJI",
    "dominica": "DMA",
    "dominican republic": "DOM",
    "ecuador": "ECU",
    "egypt": "EGY",
    "el salvador": "SLV",
    "equatorial guinea": "GNQ",
    "eritrea": "ERI",
    "estonia": "EST",
    "eswatini": "SWZ",
    "swaziland": "SWZ",
    "ethiopia": "ETH",
    "fiji": "FJI",
    "finland": "FIN",
    "france": "FRA",
    "gabon": "GAB",
    "gambia": "GMB",
    "the gambia": "GMB",
    "georgia": "GEO",
    "germany": "DEU",
    "ghana": "GHA",
    "greece": "GRC",
    "grenada": "GRD",
    "guatemala": "GTM",
    "guinea": "GIN",
    "guinea-bissau": "GNB",
    "guyana": "GUY",
    "haiti": "HTI",
    "honduras": "HND",
    "hungary": "HUN",
    "iceland": "ISL",
    "india": "IND",
    "indonesia": "IDN",
    "iran": "IRN",
    "iraq": "IRQ",
    "ireland": "IRL",
    "israel": "ISR",
    "italy": "ITA",
    "jamaica": "JAM",
    "japan": "JPN",
    "jordan": "JOR",
    "kazakhstan": "KAZ",
    "kenya": "KEN",
    "kiribati": "KIR",
    "north korea": "PRK",
    "south korea": "KOR",
    "korea": "KOR",
    "kuwait": "KWT",
    "kyrgyzstan": "KGZ",
    "laos": "LAO",
    "latvia": "LVA",
    "lebanon": "LBN",
    "lesotho": "LSO",
    "liberia": "LBR",
    "libya": "LBY",
    "liechtenstein": "LIE",
    "lithuania": "LTU",
    "luxembourg": "LUX",
    "madagascar": "MDG",
    "malawi": "MWI",
    "malaysia": "MYS",
    "maldives": "MDV",
    "mali": "MLI",
    "malta": "MLT",
    "marshall islands": "MHL",
    "mauritania": "MRT",
    "mauritius": "MUS",
    "mexico": "MEX",
    "micronesia": "FSM",
    "moldova": "MDA",
    "monaco": "MCO",
    "mongolia": "MNG",
    "montenegro": "MNE",
    "morocco": "MAR",
    "mozambique": "MOZ",
    "myanmar": "MMR",
    "burma": "MMR",
    "namibia": "NAM",
    "nauru": "NRU",
    "nepal": "NPL",
    "netherlands": "NLD",
    "holland": "NLD",
    "new zealand": "NZL",
    "nicaragua": "NIC",
    "niger": "NER",
    "nigeria": "NGA",
    "north macedonia": "MKD",
    "macedonia": "MKD",
    "norway": "NOR",
    "oman": "OMN",
    "pakistan": "PAK",
    "palau": "PLW",
    "palestine": "PSE",
    "palestinian territories": "PSE",
    "panama": "PAN",
    "papua new guinea": "PNG",
    "paraguay": "PRY",
    "peru": "PER",
    "philippines": "PHL",
    "poland": "POL",
    "portugal": "PRT",
    "qatar": "QAT",
    "romania": "ROU",
    "russia": "RUS",
    "russian federation": "RUS",
    "rwanda": "RWA",
    "saint kitts and nevis": "KNA",
    "saint lucia": "LCA",
    "saint vincent and the grenadines": "VCT",
    "samoa": "WSM",
    "san marino": "SMR",
    "sao tome and principe": "STP",
    "saudi arabia": "SAU",
    "senegal": "SEN",
    "serbia": "SRB",
    "seychelles": "SYC",
    "sierra leone": "SLE",
    "singapore": "SGP",
    "slovakia": "SVK",
    "slovenia": "SVN",
    "solomon islands": "SLB",
    "somalia": "SOM",
    "south africa": "ZAF",
    "south sudan": "SSD",
    "spain": "ESP",
    "sri lanka": "LKA",
    "sudan": "SDN",
    "suriname": "SUR",
    "sweden": "SWE",
    "switzerland": "CHE",
    "syria": "SYR",
    "syrian arab republic": "SYR",
    "taiwan": "TWN",
    "tajikistan": "TJK",
    "tanzania": "TZA",
    "thailand": "THA",
    "timor-leste": "TLS",
    "east timor": "TLS",
    "togo": "TGO",
    "tonga": "TON",
    "trinidad and tobago": "TTO",
    "tunisia": "TUN",
    "turkey": "TUR",
    "turkmenistan": "TKM",
    "tuvalu": "TUV",
    "uganda": "UGA",
    "ukraine": "UKR",
    "united arab emirates": "ARE",
    "uae": "ARE",
    "united kingdom": "GBR",
    "uk": "GBR",
    "britain": "GBR",
    "great britain": "GBR",
    "united states": "USA",
    "usa": "USA",
    "united states of america": "USA",
    "uruguay": "URY",
    "uzbekistan": "UZB",
    "vanuatu": "VUT",
    "vatican city": "VAT",
    "vatican": "VAT",
    "venezuela": "VEN",
    "vietnam": "VNM",
    "viet nam": "VNM",
    "yemen": "YEM",
    "zambia": "ZMB",
    "zimbabwe": "ZWE",
    "hong kong": "HKG",
    "macau": "MAC",
    "macao": "MAC",
    "puerto rico": "PRI",
    "guam": "GUM",
    "kosovo": "XKX",
}


def normalize_country_to_iso3(country: str) -> Optional[str]:
    """
    Convert a country name or ISO code to ISO3 format.
    Returns None if not found.
    """
    if not country:
        return None

    country_upper = country.strip().upper()

    # Already ISO3
    if country_upper in COUNTRY_CENTROIDS:
        return country_upper

    # Try lowercase name lookup
    country_lower = country.strip().lower()
    if country_lower in COUNTRY_NAME_TO_ISO3:
        return COUNTRY_NAME_TO_ISO3[country_lower]

    # Try partial matching
    for name, iso3 in COUNTRY_NAME_TO_ISO3.items():
        if name in country_lower or country_lower in name:
            return iso3

    logger.warning(f"Could not normalize country '{country}' to ISO3")
    return None


##Ask teammates if there is an api for above, used ai to generate


def get_country_centroid(iso3: str) -> Optional[Tuple[float, float]]:
    """
    Get the centroid (lat, lon) for a country by ISO3 code.
    """
    iso3_upper = iso3.upper() if iso3 else None
    return COUNTRY_CENTROIDS.get(iso3_upper)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_distance_between_countries(from_country: str, to_country: str) -> Optional[float]:
    """
    Calculate distance in km between two countries (by name or ISO3).
    Returns None if either country is not found.
    """
    from_iso3 = normalize_country_to_iso3(from_country)
    to_iso3 = normalize_country_to_iso3(to_country)

    if not from_iso3 or not to_iso3:
        return None

    from_centroid = get_country_centroid(from_iso3)
    to_centroid = get_country_centroid(to_iso3)

    if not from_centroid or not to_centroid:
        return None

    return haversine_distance(from_centroid[0], from_centroid[1], to_centroid[0], to_centroid[1])


def get_distance_score(distance_km: Optional[float], max_distance: float = 20000) -> int:
    """
    Convert distance to a score (0-100).
    Distance is the PRIMARY cost driver - closer = much higher score.

    Scoring:
    - 0-500 km: 100 points (neighboring countries - minimal logistics)
    - 500-1000 km: 85 points (very close)
    - 1000-2000 km: 70 points (regional)
    - 2000-4000 km: 55 points (continental)
    - 4000-7000 km: 40 points (intercontinental)
    - 7000-12000 km: 25 points (far)
    - 12000+ km: 10 points (very far - high logistics cost)
    """
    if distance_km is None:
        return 50  # Default middle score if unknown

    if distance_km <= 500:
        return 100
    elif distance_km <= 1000:
        return 85
    elif distance_km <= 2000:
        return 70
    elif distance_km <= 4000:
        return 55
    elif distance_km <= 7000:
        return 40
    elif distance_km <= 12000:
        return 25
    else:
        return 10


def is_same_country(country1: str, country2: str) -> bool:
    """
    Check if two country identifiers refer to the same country.
    """
    iso3_1 = normalize_country_to_iso3(country1)
    iso3_2 = normalize_country_to_iso3(country2)

    if iso3_1 and iso3_2:
        return iso3_1 == iso3_2

    # Fallback to case-insensitive string comparison
    return country1.strip().lower() == country2.strip().lower()
