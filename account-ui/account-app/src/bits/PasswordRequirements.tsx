
import Typography from "@mui/material/Typography";

const PasswordRequirements = () => {
    const msg = "Password must be at least 8 characters long, contain uppercase and lowercase letters, numbers, and at least one underscore (_).";
    return (
      <Typography variant="body1" sx={{opacity: "100%", fontSize: "1.5em"}} aria-label={msg}>
          {msg}
      </Typography>
    );
}

export default PasswordRequirements;
