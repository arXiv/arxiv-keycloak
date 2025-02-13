import React from "react";
import { Box, ToggleButtonGroup, Typography } from "@mui/material";
import BolderToggleButton from "./BolderToggleButton.tsx";

export type CategoryGroupType = "flag_group_cs" | "flag_group_econ" | "flag_group_eess" | "flag_group_math" | "flag_group_physics" | "flag_group_q_bio" | "flag_group_q_fin" | "flag_group_stat";


const CategorySelection : React.FC<{
    selectedGroups: CategoryGroupType[],
    setSelectedGroups: (groups: CategoryGroupType[]) => void,
}> = ({selectedGroups, setSelectedGroups}) => {

    const handleSelection = (_event: any, newSelection: string[]) => {
        setSelectedGroups(newSelection as unknown as CategoryGroupType[]);
    };

    return (
        <Box sx={{ border: "1px solid #ddd", borderRadius: 1, padding: 1 }}>
            <Typography variant="body1" sx={{ marginBottom: 1 }}>
                *Group(s) you would like to submit to:
            </Typography>
            <ToggleButtonGroup
                value={selectedGroups}
                onChange={handleSelection}
                aria-label="archive groups"
                sx={{ display: "flex", flexWrap: "wrap", gap: 1, p: 1 }}
            >i
                <BolderToggleButton value="flag_group_cs">cs</BolderToggleButton>
                <BolderToggleButton value="flag_group_econ">econ</BolderToggleButton>
                <BolderToggleButton value="flag_group_eess">eess</BolderToggleButton>
                <BolderToggleButton value="flag_group_math">math</BolderToggleButton>
                <BolderToggleButton value="flag_group_physics">physics</BolderToggleButton>
                <BolderToggleButton value="flag_group_q_bio">q-bio</BolderToggleButton>
                <BolderToggleButton value="flag_group_q_fin">q-fin</BolderToggleButton>
                <BolderToggleButton value="flag_group_stat">stat</BolderToggleButton>
            </ToggleButtonGroup>
        </Box>
    );
};

export default CategorySelection;
