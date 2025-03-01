import React from "react";
// import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import {RuntimeProps} from "../RuntimeContext.tsx";

const Authorship: React.FC<{props: RuntimeProps}> = ({props}) => {
    const urls = props.URLS;
    return (
        <Card sx={{ maxWidth: "lg", mb: 1 }}>
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
                <Link href={urls.needPaperPassword}> the Claim Ownership with a password form</Link>.
                        </ListItem>
                        <ListItem >
                If you do not have the paper password or are claiming multiple papers, use
                <Link href={urls.requestOwnership}> the Claim Authorship form</Link>.
                        </ListItem>
                        <ListItem >
                For more information, see the help page on <Link href={urls.authorityRecord}> authority records</Link>.
                            </ListItem>
                        <ListItem >

                            <Typography component="span">
                                You are encouraged to associate your{" "}
                                <Link href={urls.authorIdentifier}>ORCID</Link>{" "}
                                <Link href={urls.orcidOrg}>
                                    <img
                                        src="/static/images/icons/orcid_16x16.png"
                                        alt="ORCID logo"
                                        style={{ position: "relative", bottom: "-3px" }}
                                    />
                                </Link>{" "}
                                with your arXiv account. ORCID iDs are standard, persistent identifiers for
                                research authors. ORCID iDs will gradually supersede the role of the arXiv{" "}
                                <Link href={urls.authorIdentifier}>
                                    author identifier
                                </Link>
                                . To associate your ORCID iD with your arXiv account, please confirm your
                                ORCID iD.
                            </Typography>
                        </ListItem>
                    </Typography>

                </List>
            </CardContent>
        </Card>
    );
};

export default Authorship;
