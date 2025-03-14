import React from "react";
// import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import CardContent from "@mui/material/CardContent";

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
    return (
        <Card>
            <CardHeader title={"Author Information"}  />
            <CardContent>
                You own {ownerCount} article{ownerCount !== 1 ? "s" : ""}, have
                submitted {submitCount} article{submitCount !== 1 ? "s" : ""} and are
                registered as the author of {authorCount} article
                {authorCount !== 1 ? "s" : ""}.

            <p>
                Are you incorrectly registered as an author or a non-author of any
                articles you own?
                <br />
                If so, use <a href="/auth/change-author-status">the Change Author Status form</a>
            </p>

            <p>
                Are there articles you are an author of on arXiv that are not listed
                here?
                <br />
                If you have the paper password use
                <a href="/user-account/claim-document-ownership"> the Claim Ownership with a password form</a>
                <br />
                If you do not have the paper password or are claiming multiple papers
                use <a href="/auth/request-ownership">the Claim Authorship form</a>.
                <br />
                For more information please see our help page on
                <a href="https://info.arxiv.org/help/authority"> authority records</a>.
            </p>

            {authorId ? (
                <p>
                    Your public author identifier is
                    <a href={`https://arxiv.org/a/${authorId}`}> {authorId}</a> and may be used by other services
                    to access the list of articles authored by you, see
                    <a href="https://info.arxiv.org/help/author_identifiers">
                        author identifier help
                    </a>
                    .
                </p>
            ) : authorCount >= 1 ? (
                <p>
                    No public author identifier has been set for your account, see
                    <a href="https://info.arxiv.org/help/author_identifiers">
                        author identifier help
                    </a>
                    or you may <a href="/set_author_id">set a public author identifier</a>.
                </p>
            ) : null}

            {orcidId && orcidAuth ? (
                <p>
                    Your <a href="https://info.arxiv.org/help/orcid">ORCID iD</a> is
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
