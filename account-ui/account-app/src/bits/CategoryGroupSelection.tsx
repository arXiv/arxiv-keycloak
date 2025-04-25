import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";

// import BolderToggleButton from "./BolderToggleButton.tsx";

export type CategoryGroupType = "grp_physics" | "grp_math" | "grp_cs" | "grp_q-econ" | "grp_q-bio" | "grp_q-fin" | "grp_q-stat" | "grp_eess";

const CategoryOption : React.FC<{ value: string, checked: boolean, label: string, callback: (event: React.ChangeEvent<HTMLInputElement>) => void }> = ({value, checked, label, callback}) => {
    return (
        <FormControlLabel control={<Checkbox key={value} checked={checked} value={value} onChange={callback} />} label={label} />
    );
}

const CategoryGroupSelection : React.FC<{
    selectedGroups: CategoryGroupType[],
    setSelectedGroups: (groups: CategoryGroupType[]) => void,
    isSmallScreen: boolean,
}> = ({selectedGroups, setSelectedGroups, isSmallScreen}) => {

    const handleSelection = (event: React.ChangeEvent<HTMLInputElement>) => {
        const checked = event.target.checked;
        const value: CategoryGroupType = event.target.value as unknown as CategoryGroupType;
        if (checked) {
            if (!selectedGroups.includes(value))
                setSelectedGroups(selectedGroups.concat(value));
        } else {
            setSelectedGroups(selectedGroups.filter((group) => group !== value));
        }
    };

    const choices: {value: CategoryGroupType, label: string}[] = [
            {value: "grp_cs", label: "Computer Science"},
            {value: "grp_q-econ", label: "Economics"},
            {value: "grp_eess", label: "Electrical Engineering and Systems Science"},
            {value: "grp_math", label: "Mathematics"},
            {value: "grp_physics", label: "Physics"},
            {value: "grp_q-bio", label: "Quantitative Biology"},
            {value: "grp_q-fin", label: "Quantitative Finance"},
            {value: "grp_q-stat", label: "Statistics"},
        ];

    const prompt = selectedGroups.length == 0 ? (<Typography variant="caption" color={"error"} sx={{fontSize: "1rem"}}> Please select at least one </Typography>) : null;

    return (
        <Box>
            <Typography variant="body1" sx={{ marginBottom: 1 }}>
                Categorie(s) you would like to submit to (required):
                {
                    prompt
                }
            </Typography>
            <FormGroup
                aria-label="archive groups"
                sx={{
                    display: "grid",
                    gridTemplateColumns: isSmallScreen ? "repeat(2, 1fr)" : "repeat(4, 1fr)",
                    gap: 1,
                    p:1 }}
            >
                {
                    choices.map((choice) =>  (
                        <CategoryOption
                            checked={selectedGroups.includes(choice.value)}
                                         value={choice.value} label={choice.label} callback={handleSelection} />))
                }
            </FormGroup>
        </Box>
    );
};

export default CategoryGroupSelection;
