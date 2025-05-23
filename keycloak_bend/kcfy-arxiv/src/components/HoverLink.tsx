import React, {ReactNode} from "react";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";

interface HoverLinkProps {
    href: string;
    label: ReactNode;
}
const HoverLink : React.FC<HoverLinkProps> = ({href, label}) => {
    return (
        <Link
            href={href}
            sx={{
                alignItems: "center",
                textDecoration: "none",
                color: "black", // Use default text color
                "&:hover": { color: "primary.main", textDecoration: "underline" }, // Change color on hover
                display: "inline-flex",
                width: "auto",
            }}
        >
            <Typography variant="body2" sx={{display: "inline"}}>{label}</Typography>
        </Link>
    )
}

export default HoverLink;
