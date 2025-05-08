import React, {useContext} from "react";
// import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import CardContent from "@mui/material/CardContent";
import { RuntimeContext } from "../RuntimeContext";
// import {useNavigate} from "react-router-dom";
import Link from "@mui/material/Link";
import { Link as RouterLink } from 'react-router-dom';
import AuthorInfoTable from "./AuthorInfoTable.tsx";
import Typography from "@mui/material/Typography/Typography";

interface ArticleInfoProps {
    ownerCount: number;
    submitCount: number;
    authorCount: number;
}

const ArticleInfo: React.FC<ArticleInfoProps> = ({
                                                   ownerCount,
                                                   submitCount,
                                                   authorCount,
                                               }) => {
    const runtimeProps = useContext(RuntimeContext);
    // const navigate = useNavigate();
    return (
        <Card>
            <CardHeader title={"Article Information"}  />
            <CardContent sx={{py: 0}}>
                <AuthorInfoTable ownerCount={ownerCount} submitCount={submitCount}  authorCount={authorCount}  />
            <p>
                Are you incorrectly registered as an author or a non-author of any
                articles you own? If so, update the authorship status below.
            </p>

                <Typography component="div" sx={{ mt: 2 }}>
                    Are there articles you are an author of on arXiv that are not listed here?
                    <ul style={{ paddingLeft: '1.5em', marginTop: 0 }}>
                        <li>
                            If you have the paper password, use&nbsp;
                            <Link component={RouterLink} to={runtimeProps.URLS.userClaimDocumentOwnership}>
                                the Claim Ownership with a password form
                            </Link>
                            .
                        </li>
                        <li>
                            If you do not have the paper password or are claiming multiple papers, use&nbsp;
                            <Link component={RouterLink} to={runtimeProps.URLS.userRequestDocumentOwnership}>
                                the Claim Authorship form
                            </Link>
                            .
                        </li>
                        <li>
                            For more information, please see our help page on&nbsp;
                            <Link href="https://info.arxiv.org/help/authority" target="_blank" rel="noreferrer">
                                authority records
                            </Link>.
                        </li>
                    </ul>
                </Typography>

            </CardContent>
        </Card>
    );
};

export default ArticleInfo;
