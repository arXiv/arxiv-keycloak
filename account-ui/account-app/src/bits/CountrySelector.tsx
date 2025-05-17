import React, {useContext, useEffect, useState} from "react";
import Box from "@mui/material/Box";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";

import {paths as adminApi} from "../types/admin-api";
import {RuntimeContext} from "../RuntimeContext.tsx";

type CountriesType = adminApi['/v1/countries/iso2']['get']['responses']['200']['content']['application/json'];


// Define a type for country options
interface Country {
    id: string;
    country_name: string;
}

// List of countries with ISO 3166-1 Alpha-2 codes
interface CountrySelectProps {
    onSelect: (countryId: string) => void;
    selectedCountry: string;
}

const CountrySelector: React.FC<CountrySelectProps> = ({ onSelect, selectedCountry }) => {
    const runtimeProps = useContext(RuntimeContext);
    const [countries, setCountries] = useState<CountriesType>([
        { id: "", country_name: "Please select", continent: ""  },
        { id: "US", country_name: "United States", continent: ""  },
        { id: "CA", country_name: "Canada", continent: ""  },
        { id: "GB", country_name: "United Kingdom", continent: ""  },
        { id: "DE", country_name: "Germany", continent: ""  },
        { id: "FR", country_name: "France", continent: ""  },
        { id: "AU", country_name: "Australia", continent: ""  },
        { id: "JP", country_name: "Japan", continent: ""  },
        { id: "CN", country_name: "China", continent: ""  },
        { id: "IN", country_name: "India", continent: ""  },
        { id: "BR", country_name: "Brazil", continent: ""  },
        { id: "ZA", country_name: "South Africa", continent: ""  },
        { id: "MX", country_name: "Mexico", continent: ""  },
        { id: "IT", country_name: "Italy", continent: ""  },
        { id: "ES", country_name: "Spain", continent: ""  },
        { id: "RU", country_name: "Russia", continent: ""  },
        { id: "NL", country_name: "Netherlands", continent: ""  },
        { id: "SE", country_name: "Sweden", continent: ""  },
        { id: "NO", country_name: "Norway", continent: ""  },
        { id: "DK", country_name: "Denmark", continent: ""  },
        { id: "FI", country_name: "Finland", continent: ""  },
        { id: "KR", country_name: "South Korea", continent: ""  },
        { id: "NZ", country_name: "New Zealand", continent: ""  }
    ]);

    useEffect(() => {
        const fetchCountries = async () => {
            try {
                const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/countries/iso2`);
                const result: CountriesType = await response.json();
                const opts = [{ id: "", country_name: "Please select", continent: ""  }].concat(result);
                setCountries( opts);
            } catch (error) {
                console.error("Failed to fetch group info", error);
            }
        };

        fetchCountries();
    }, [runtimeProps.ADMIN_API_BACKEND_URL]);

    const handleChange = (_event: React.SyntheticEvent, newValue: Country | null) => {
        if (newValue) {
            onSelect(newValue.id);
        }
    };


    console.log(selectedCountry?.toUpperCase() + "|" + JSON.stringify(countries.find((country) => country.id.toUpperCase() === selectedCountry?.toUpperCase())));

    return (
        <Box sx={{ flex: 2 }}>
            <Autocomplete
                options={countries}
                getOptionLabel={(option) => option.country_name} // Show country name
                value={countries.find((country) => country.id.toUpperCase() === selectedCountry?.toUpperCase())}
                onChange={handleChange}
                renderInput={(params) => (
                    <TextField {...params} size="small" variant="outlined" label="Country (required)"
                               slotProps={{
                                   inputLabel: {
                                       shrink: true,
                                       sx: {
                                           ...params.InputLabelProps,
                                           position: 'static',
                                           transform: 'none',
                                           fontSize: '1em',
                                           color: 'black',
                                           fontWeight: 'bold',
                                           pb: '3px',
                                       },
                                   },
                                   input: {
                                       ...params.InputProps,
                                       notched: false,
                                   }
                               }}
                    />
                )}
            />
        </Box>
    );
};

export default CountrySelector;
