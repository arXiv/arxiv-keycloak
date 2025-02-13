import { ToggleButton } from "@mui/material";
import { styled } from "@mui/system";

// Styled ToggleButton with better visibility
const BolderToggleButton = styled(ToggleButton)({
    // Stronger border border: "3px solid #B31B1B",
    color: "black", // Text color
    fontWeight: "bold",
    "&.Mui-selected": {
        backgroundColor: "#000000 !important",
        color: "white !important",
    },
    "&:hover": {
        backgroundColor: "#a0a0a0",
    },
    "&.Mui-disabled": {
        opacity: 0.5,
    },
});

export default BolderToggleButton;

