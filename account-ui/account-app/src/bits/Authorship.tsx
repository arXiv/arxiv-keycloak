import React from "react";
// import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";

const Authorship: React.FC = () => {
    return (
        <Card sx={{ width: "90vw", maxWidth: "800px", mb: 1 }}>
            <CardContent>
                <Typography variant="h5" gutterBottom>
                    Authorship
                </Typography>

                <List>
                    <Typography variant="body1">
                    <ListItem >
                            Are there articles you are an author of on arXiv that are not listed here?
                    </ListItem>
                        <ListItem >
                If you have the paper password, use
                <Link href="/auth/need-paper-password"> the Claim Ownership with a password form</Link>.
                        </ListItem>
                        <ListItem >
                If you do not have the paper password or are claiming multiple papers, use
                <Link href="/auth/request-ownership"> the Claim Authorship form</Link>.
                        </ListItem>
                        <ListItem >
                For more information, see the help page on <Link href="https://info.arxiv.org/help/authority"> authority records</Link>.
                            </ListItem>
                    </Typography>

                </List>
            </CardContent>
        </Card>
    );
};

export default Authorship;
