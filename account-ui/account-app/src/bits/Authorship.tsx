import React from "react";
import { Typography, Link, Box} from "@mui/material";


const Authorship: React.FC = () => {
    return (
        <Box sx={{ mb: 3, color: "black" }}>
            <Typography variant="body1">
                Are there articles you are an author of on arXiv that are not listed here?
            </Typography>
            <Typography variant="body1">
                If you have the paper password, use
                <Link href="/auth/need-paper-password"> the Claim Ownership with a password form</Link>.
            </Typography>
            <Typography variant="body1">
                If you do not have the paper password or are claiming multiple papers, use
                <Link href="/auth/request-ownership"> the Claim Authorship form</Link>.
            </Typography>
            <Typography variant="body1">
                For more information, see the help page on <Link href="https://info.arxiv.org/help/authority"> authority records</Link>.
            </Typography>
        </Box>
    );
};

export default Authorship;
