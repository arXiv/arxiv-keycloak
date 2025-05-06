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
    authorId?: string | null;
    orcidId?: string | null;
    orcidAuth?: boolean;
}

const ArticleInfo: React.FC<ArticleInfoProps> = ({
                                                   ownerCount,
                                                   submitCount,
                                                   authorCount,
                                                   authorId,
                                                   orcidId,
                                                   orcidAuth,
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
            {authorId ? (
                <p>
                    Your public author identifier is
                    <a href={`https://arxiv.org/a/${authorId}`} target="_blank"> {authorId}</a> and may be used by other services
                    to access the list of articles authored by you, see
                    <a href="https://info.arxiv.org/help/author_identifiers" target="_blank">
                        author identifier help
                    </a>
                    .
                </p>
            ) : authorCount >= 1 ? (
                <p>
                    No public author identifier has been set for your account, see
                    <a href="https://info.arxiv.org/help/author_identifiers" target="_blank">
                        author identifier help
                    </a>
                    or you may <a href="/set_author_id">set a public author identifier</a>.
                </p>
            ) : null}

            {orcidId && orcidAuth ? (
                <p>
                    Your <a href="https://info.arxiv.org/help/orcid" target="_blank">ORCID iD</a>{" is "}
                    <a href={`https://arxiv.org/a/${orcidId}`}>{orcidId}</a>.
                </p>
            ) : (
                <p>
                    You are encouraged to associate your
                    <a href="https://info.arxiv.org/help/orcid"> ORCID</a> with your
                    arXiv account. ORCID iDs are standard, persistent identifiers for
                    research authors.
                    {orcidId && !orcidAuth ? (
                        <>
                            Our search indicates that you may already have an
                            <a href="https://info.arxiv.org/help/orcid"> ORCID</a>:
                            <a href={`https://arxiv.org/a/${orcidId}`}> {orcidId}</a>. If this is the wrong iD, you may
                            change it below.
                        </>
                    ) : null}
                    ORCID iDs will gradually supersede the role of the arXiv
                    <a href="https://info.arxiv.org/help/author_identifiers">
                        author identifier
                    </a>
                    . To associate your ORCID iD with your arXiv account, please
                    <a href="/user/confirm_orcid_id">
                        confirm {orcidId && !orcidAuth ? "or correct" : ""} your ORCID iD
                    </a>
                    .
                </p>
            )}
            </CardContent>
        </Card>
    );
};

export default ArticleInfo;
