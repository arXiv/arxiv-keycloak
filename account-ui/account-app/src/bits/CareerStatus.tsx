import React from "react";
import TextField from "@mui/material/TextField";
import Autocomplete from "@mui/material/Autocomplete";

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

    const displayLabel = (option: string) => {
        return option === "Unknown" ? "Please select" : option;
    };

    return (
            <Autocomplete
                options={career_status_options}
                value={careereStatus}
                onChange={handleChange}
                getOptionLabel={displayLabel}
                renderInput={(params) => (
                    <TextField {...params} size="small" variant="outlined"
                        label="Career Stage (required)"
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
    );
};

export default CareerStatusSelect;
