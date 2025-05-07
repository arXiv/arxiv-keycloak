import React from "react";
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
    { code: "", country: "Please select" },
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
    onSelect: (countryCode: string) => void;
    selectedCountry: string;
}

const CountrySelector: React.FC<CountrySelectProps> = ({ onSelect, selectedCountry }) => {

    const handleChange = (_event: React.SyntheticEvent, newValue: Country | null) => {
        if (newValue) {
            onSelect(newValue.code);
        }
    };

    console.log(selectedCountry?.toUpperCase() + "|" + JSON.stringify(countries.find((country) => country.code.toUpperCase() === selectedCountry?.toUpperCase())));
    return (
        <Box sx={{ flex: 2 }}>
            <Autocomplete
                options={countries}
                getOptionLabel={(option) => option.country} // Show country name
                value={countries.find((country) => country.code.toUpperCase() === selectedCountry?.toUpperCase())}
                onChange={handleChange}
                renderInput={(params) => (
                    <TextField {...params} size="small" label="Country (required)" variant="outlined" />
                )}
            />
        </Box>
    );
};

export default CountrySelector;
