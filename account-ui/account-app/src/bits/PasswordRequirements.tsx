
import Typography from "@mui/material/Typography";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";

const PasswordRequirements = () => {
    const passwordRequirements = [
        "8 characters or more in length",
        "May contain uppercase letters, lowercase letters, numbers and special characters",
        "Must contain at least one special character"
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
