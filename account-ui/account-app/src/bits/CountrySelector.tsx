import React, { useState } from "react";
import { Box, Autocomplete, TextField } from "@mui/material";

// Define a type for the country options
type Country = string;

// List of country names
const countries: Country[] = [
    "United States", "Canada", "United Kingdom", "Germany", "France",
    "Australia", "Japan", "China", "India", "Brazil", "South Africa",
    "Mexico", "Italy", "Spain", "Russia", "Netherlands", "Sweden",
    "Norway", "Denmark", "Finland", "South Korea", "New Zealand"
];

interface CountrySelectProps {
    onSelect?: (country: Country | null) => void;
}

const CountrySelector: React.FC<CountrySelectProps> = ({ onSelect }) => {
    const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);

    const handleChange = (_event: React.SyntheticEvent, newValue: Country | null) => {
        setSelectedCountry(newValue);
        if (onSelect) onSelect(newValue);
    };

    return (
        <Box sx={{flex: 2}}>
            <Autocomplete
                options={countries}
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
