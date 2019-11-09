from typing import Dict

CONTINENT_DICTIONARY: Dict[str, str] = {'AF': 'Africa', 'NA': 'North America', 'OC': 'Oceania', 'AN': 'Antarctica',
                                        'AS': 'Asia', 'EU': 'Europe',
                                        'SA': 'South America', 'WW': 'World', 'World Wide': 'World',
                                        'na': 'North America', 'na (c)': 'North America',
                                        'na (C)': 'North America', 'na(c)': 'North America', 'na(C)': 'North America',
                                        'NA (c)': 'North America',
                                        'NA (C)': 'North America', 'NA(c)': 'North America', 'NA(C)': 'North America',
                                        'north america': 'North America',
                                        'north america (c)': 'North America', 'north america (C)': 'North America',
                                        'north america(c)': 'North America',
                                        'north america(C)': 'North America', 'North America': 'North America',
                                        'North America (c)': 'North America',
                                        'North America (C)': 'North America', 'North America(c)': 'North America',
                                        'North America(C)': 'North America',
                                        'NORTH AMERICA': 'North America', 'NORTH AMERICA (c)': 'North America',
                                        'NORTH AMERICA (C)': 'North America',
                                        'NORTH AMERICA(c)': 'North America', 'NORTH AMERICA(C)': 'North America',
                                        'North america': 'North America',
                                        'North america (c)': 'North America', 'North america (C)': 'North America',
                                        'North america(c)': 'North America',
                                        'North america(C)': 'North America', 'Northamerica': 'North America',
                                        'Northamerica (c)': 'North America',
                                        'Northamerica (C)': 'North America', 'Northamerica(c)': 'North America',
                                        'Northamerica(C)': 'North America',
                                        'NorthAmerica': 'North America', 'NorthAmerica (c)': 'North America',
                                        'NorthAmerica (C)': 'North America',
                                        'NorthAmerica(c)': 'North America', 'NorthAmerica(C)': 'North America',
                                        'AN (c)': 'Antarctica',
                                        'AN (C)': 'Antarctica', 'AN(c)': 'Antarctica', 'AN(C)': 'Antarctica',
                                        'an': 'Antarctica', 'an (c)': 'Antarctica',
                                        'an (C)': 'Antarctica', 'an(c)': 'Antarctica', 'an(C)': 'Antarctica',
                                        'ANTARCTICA': 'Antarctica',
                                        'ANTARCTICA (c)': 'Antarctica', 'ANTARCTICA (C)': 'Antarctica',
                                        'ANTARCTICA(c)': 'Antarctica',
                                        'ANTARCTICA(C)': 'Antarctica', 'antarctica': 'Antarctica',
                                        'antarctica (c)': 'Antarctica',
                                        'antarctica (C)': 'Antarctica', 'antarctica(c)': 'Antarctica',
                                        'antarctica(C)': 'Antarctica',
                                        'Antarctica': 'Antarctica', 'Antarctica (c)': 'Antarctica',
                                        'Antarctica (C)': 'Antarctica',
                                        'Antarctica(c)': 'Antarctica', 'Antarctica(C)': 'Antarctica',
                                        'sa': 'South America', 'sa (c)': 'South America',
                                        'sa (C)': 'South America', 'sa(c)': 'South America', 'sa(C)': 'South America',
                                        'SA (c)': 'South America',
                                        'SA (C)': 'South America', 'SA(c)': 'South America', 'SA(C)': 'South America',
                                        'south america': 'South America',
                                        'south america (c)': 'South America', 'south america (C)': 'South America',
                                        'south america(c)': 'South America',
                                        'south america(C)': 'South America', 'South America': 'South America',
                                        'South America (c)': 'South America',
                                        'South America (C)': 'South America', 'South America(c)': 'South America',
                                        'South America(C)': 'South America',
                                        'SOUTH AMERICA': 'South America', 'SOUTH AMERICA (c)': 'South America',
                                        'SOUTH AMERICA (C)': 'South America',
                                        'SOUTH AMERICA(c)': 'South America', 'SOUTH AMERICA(C)': 'South America',
                                        'South america': 'South America',
                                        'South america (c)': 'South America', 'South america (C)': 'South America',
                                        'South america(c)': 'South America',
                                        'South america(C)': 'South America', 'Southamerica': 'South America',
                                        'Southamerica (c)': 'South America',
                                        'Southamerica (C)': 'South America', 'Southamerica(c)': 'South America',
                                        'Southamerica(C)': 'South America',
                                        'SouthAmerica': 'South America', 'SouthAmerica (c)': 'South America',
                                        'SouthAmerica (C)': 'South America',
                                        'SouthAmerica(c)': 'South America', 'SouthAmerica(C)': 'South America',
                                        'AS (c)': 'Asia', 'AS (C)': 'Asia',
                                        'AS(c)': 'Asia', 'AS(C)': 'Asia', 'as': 'Asia', 'as (c)': 'Asia',
                                        'as (C)': 'Asia', 'as(c)': 'Asia',
                                        'as(C)': 'Asia', 'asia': 'Asia', 'asia (c)': 'Asia', 'asia (C)': 'Asia',
                                        'asia(c)': 'Asia', 'asia(C)': 'Asia',
                                        'Asia': 'Asia', 'Asia (c)': 'Asia', 'Asia (C)': 'Asia', 'Asia(c)': 'Asia',
                                        'Asia(C)': 'Asia', 'ASIA': 'Asia',
                                        'ASIA (c)': 'Asia', 'ASIA (C)': 'Asia', 'ASIA(c)': 'Asia', 'ASIA(C)': 'Asia',
                                        'eu': 'Europe', 'eu (c)': 'Europe',
                                        'eu (C)': 'Europe', 'eu(c)': 'Europe', 'eu(C)': 'Europe', 'EU (c)': 'Europe',
                                        'EU (C)': 'Europe',
                                        'EU(c)': 'Europe', 'EU(C)': 'Europe', 'EUROPE': 'Europe',
                                        'EUROPE (c)': 'Europe', 'EUROPE (C)': 'Europe',
                                        'EUROPE(c)': 'Europe', 'EUROPE(C)': 'Europe', 'Europe': 'Europe',
                                        'Europe (c)': 'Europe', 'Europe (C)': 'Europe',
                                        'Europe(c)': 'Europe', 'Europe(C)': 'Europe', 'europe': 'Europe',
                                        'europe (c)': 'Europe', 'europe (C)': 'Europe',
                                        'europe(c)': 'Europe', 'europe(C)': 'Europe', 'AF (c)': 'Africa',
                                        'AF (C)': 'Africa', 'AF(c)': 'Africa',
                                        'AF(C)': 'Africa', 'af': 'Africa', 'af (c)': 'Africa', 'af (C)': 'Africa',
                                        'af(c)': 'Africa', 'af(C)': 'Africa',
                                        'AFRICA': 'Africa', 'AFRICA (c)': 'Africa', 'AFRICA (C)': 'Africa',
                                        'AFRICA(c)': 'Africa', 'AFRICA(C)': 'Africa',
                                        'Africa': 'Africa', 'Africa (c)': 'Africa', 'Africa (C)': 'Africa',
                                        'Africa(c)': 'Africa', 'Africa(C)': 'Africa',
                                        'africa': 'Africa', 'africa (c)': 'Africa', 'africa (C)': 'Africa',
                                        'africa(c)': 'Africa', 'africa(C)': 'Africa',
                                        'OC (c)': 'Oceania', 'OC (C)': 'Oceania', 'OC(c)': 'Oceania',
                                        'OC(C)': 'Oceania', 'oc': 'Oceania',
                                        'oc (c)': 'Oceania', 'oc (C)': 'Oceania', 'oc(c)': 'Oceania',
                                        'oc(C)': 'Oceania', 'oceania': 'Oceania',
                                        'oceania (c)': 'Oceania', 'oceania (C)': 'Oceania', 'oceania(c)': 'Oceania',
                                        'oceania(C)': 'Oceania',
                                        'Oceania': 'Oceania', 'Oceania (c)': 'Oceania', 'Oceania (C)': 'Oceania',
                                        'Oceania(c)': 'Oceania',
                                        'Oceania(C)': 'Oceania', 'OCEANIA': 'Oceania', 'OCEANIA (c)': 'Oceania',
                                        'OCEANIA (C)': 'Oceania',
                                        'OCEANIA(c)': 'Oceania', 'OCEANIA(C)': 'Oceania', 'ww': 'World',
                                        'ww (c)': 'World', 'ww (C)': 'World',
                                        'ww(c)': 'World', 'ww(C)': 'World', 'WW (c)': 'World', 'WW (C)': 'World',
                                        'WW(c)': 'World', 'WW(C)': 'World',
                                        'World Wide (c)': 'World', 'World Wide (C)': 'World', 'World Wide(c)': 'World',
                                        'World Wide(C)': 'World',
                                        'WORLD WIDE': 'World', 'WORLD WIDE (c)': 'World', 'WORLD WIDE (C)': 'World',
                                        'WORLD WIDE(c)': 'World',
                                        'WORLD WIDE(C)': 'World', 'world wide': 'World', 'world wide (c)': 'World',
                                        'world wide (C)': 'World',
                                        'world wide(c)': 'World', 'world wide(C)': 'World', 'World wide': 'World',
                                        'World wide (c)': 'World',
                                        'World wide (C)': 'World', 'World wide(c)': 'World', 'World wide(C)': 'World',
                                        'Worldwide': 'World',
                                        'Worldwide (c)': 'World', 'Worldwide (C)': 'World', 'Worldwide(c)': 'World',
                                        'Worldwide(C)': 'World',
                                        'WorldWide': 'World', 'WorldWide (c)': 'World', 'WorldWide (C)': 'World',
                                        'WorldWide(c)': 'World',
                                        'WorldWide(C)': 'World', 'WORLD': 'World', 'WORLD (c)': 'World',
                                        'WORLD (C)': 'World', 'WORLD(c)': 'World',
                                        'WORLD(C)': 'World', 'world': 'World', 'world (c)': 'World',
                                        'world (C)': 'World', 'world(c)': 'World',
                                        'world(C)': 'World', 'World': 'World', 'World (c)': 'World',
                                        'World (C)': 'World', 'World(c)': 'World',
                                        'World(C)': 'World'}