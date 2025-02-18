import React, { useState } from "react";
import Box from "@mui/material/Box";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";

// Define a type for country options
interface Country {
    code: string;
    country: string;
}

// List of countries with ISO 3166-1 Alpha-2 codes
const countries: Country[] = [
    { code: "US", country: "United States" },
    { code: "CA", country: "Canada" },
    { code: "GB", country: "United Kingdom" },
    { code: "DE", country: "Germany" },
    { code: "FR", country: "France" },
    { code: "AU", country: "Australia" },
    { code: "JP", country: "Japan" },
    { code: "CN", country: "China" },
    { code: "IN", country: "India" },
    { code: "BR", country: "Brazil" },
    { code: "ZA", country: "South Africa" },
    { code: "MX", country: "Mexico" },
    { code: "IT", country: "Italy" },
    { code: "ES", country: "Spain" },
    { code: "RU", country: "Russia" },
    { code: "NL", country: "Netherlands" },
    { code: "SE", country: "Sweden" },
    { code: "NO", country: "Norway" },
    { code: "DK", country: "Denmark" },
    { code: "FI", country: "Finland" },
    { code: "KR", country: "South Korea" },
    { code: "NZ", country: "New Zealand" }
];

interface CountrySelectProps {
    onSelect?: (countryCode: string | null) => void;
}

const CountrySelector: React.FC<CountrySelectProps> = ({ onSelect }) => {
    const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);

    const handleChange = (_event: React.SyntheticEvent, newValue: Country | null) => {
        setSelectedCountry(newValue);
        if (onSelect) onSelect(newValue ? newValue.code : null);
    };

    return (
        <Box sx={{ flex: 2 }}>
            <Autocomplete
                options={countries}
                getOptionLabel={(option) => option.country} // Show country name
                value={selectedCountry}
                onChange={handleChange}
                renderInput={(params) => (
                    <TextField {...params} label="Country *" variant="outlined" />
                )}
            />
        </Box>
    );
};

export default CountrySelector;
