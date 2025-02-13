import React, { useState } from "react";
import { Box, Autocomplete, TextField } from "@mui/material";

type CareerStatus = string;

const careerStatusList: CareerStatus[] = [
    "Unknown", "Professor", "Post Graduate", "Under graduate", "Staff"
];

interface CareerStatusProps {
    onSelect?: (country: CareerStatus | null) => void;
}

const CareerStatusSelect: React.FC<CareerStatusProps> = ({ onSelect }) => {
    const [careereStatus, setCareereStatus] = useState<CareerStatus | null>(null);

    const handleChange = (_event: React.SyntheticEvent, newValue: CareerStatus | null) => {
        setCareereStatus(newValue);
        if (onSelect) onSelect(newValue);
    };

    return (
        <Box sx={{flex: 2}}>
            <Autocomplete
                options={careerStatusList}
                value={careereStatus}
                onChange={handleChange}
                renderInput={(params) => (
                    <TextField {...params} label="Career Status *" variant="outlined" />
                )}
            />
        </Box>
    );
};

export default CareerStatusSelect;
