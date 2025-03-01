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
}> = ({selectedGroups, setSelectedGroups}) => {

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
            {value: "grp_cs", label: "CS"},
            {value: "grp_q-econ", label: "Econ"},
            {value: "grp_eess", label: "EESS"},
            {value: "grp_math", label: "Math"},
            {value: "grp_physics", label: "Physics"},
            {value: "grp_q-bio", label: "Q_Bio"},
            {value: "grp_q-fin", label: "Q_Fin"},
            {value: "grp_q-stat", label: "Stat"}
        ];

    const prompt = selectedGroups.length == 0 ? (<Typography variant="caption"> Please select at least one </Typography>) : null;

    return (
        <Box sx={{ border: "1px solid #ddd", borderRadius: 1, padding: 1 }}>
            <Typography variant="body1" sx={{ marginBottom: 1 }}>
                *Group(s) you would like to submit to:
                {
                    prompt
                }
            </Typography>
            <FormGroup
                aria-label="archive groups"
                sx={{ display: "flex", flexDirection: "row", flexWrap: "wrap", gap: 1, p: 1 }}
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
