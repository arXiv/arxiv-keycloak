
import Typography from "@mui/material/Typography";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import {PASSWORD_MIN_LENGTH} from "./validators.ts";

const PasswordRequirements = () => {
    const passwordRequirements = [
        `${PASSWORD_MIN_LENGTH} characters or more`,
        "Can contain letters, numbers, and special characters",
        "16 or more characters strongly recommended",
        "Common and weak passwords are prohibited by arXiv",
    ];

    return (<Typography sx={{mt: 2}}>
        Password requirements
        <List component="ol" sx={{ listStyleType: 'decimal', pl: 3, py: 0 }}>
            {
                passwordRequirements.map((paragraph) => (
                    <ListItem component="li" sx={{ display: 'list-item', pl: 0, py: 0 }} >
                        <ListItemText>
                            {paragraph}
                        </ListItemText>
                    </ListItem>
                ))
            }
        </List>
    </Typography>);
}

export default PasswordRequirements;
