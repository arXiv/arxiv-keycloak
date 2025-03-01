import React from "react";
import Box from "@mui/material/Box";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";

import { paths } from "../types/aaa-api.ts";

export type AccountProfileType = paths["/account/profile/{user_id}"]["get"]["responses"]["200"]["content"]["application/json"];
export type CareerStatusType = AccountProfileType['career_status'];

const career_status_options = ["Unknown", "Staff", "Professor", "Post Doc", "Grad Student", "Other"];

interface CareerStatusProps {
    onSelect: (careerStatus: CareerStatusType) => void;
    careereStatus: CareerStatusType;
}

const CareerStatusSelect: React.FC<CareerStatusProps> = ({ onSelect, careereStatus }) => {

    const handleChange = (_event: React.SyntheticEvent, newValue: string | null) => {
        if (newValue) {
            onSelect(newValue as unknown as CareerStatusType);
        }
    };

    return (
        <Box sx={{flex: 2}}>
            <Autocomplete
                options={career_status_options}
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
