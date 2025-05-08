import React, {useCallback, useContext, useEffect, useState} from "react";
import CircularProgress from "@mui/material/CircularProgress";
import {useNotification} from "../NotificationContext";
import {fetchPlus} from "../fetchPlus.ts";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import CardContent from "@mui/material/CardContent";
import { RuntimeContext } from "../RuntimeContext";
import Link from "@mui/material/Link";
import { Link as RouterLink } from 'react-router-dom';
import AuthorInfoTable from "../bits/AuthorInfoTable";
import Typography from "@mui/material/Typography/Typography";
import NavigateLink from "../bits/NavigateLink";

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
    return (
        <Card>
            <CardHeader title={"Article Information"}  />
            <CardContent sx={{py: 0}}>
                <AuthorInfoTable ownerCount={ownerCount} submitCount={submitCount}  authorCount={authorCount}  />
                <p>
                    {"Are you incorrectly registered as an author or a non-author of any articles you own? If so, update the authorship status "}
                    <NavigateLink to={"/user-account/owned-documents"} >
                        here.
                    </NavigateLink>
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


const YourDocuments: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isSubmissionLoading, setIsSubmissionLoading] = useState<boolean>(false);
    const [allPaperCount, setAllPaperCount] = useState<number>(0);
    const [totalSubmissions, setTotalSubmissions] = useState<number>(0);
    const {showNotification} = useNotification();

    useEffect(() => {
        async function fetchSubmissions() {
            if (!runtimeProps.currentUser)
                return;

            // const interestedIds = Object.values(submissinStatusList).filter(status => status.group === "current" || status.group === "processing");
            const start = 0;
            const end = 1;
            const query = new URLSearchParams();

            query.append("submitter_id", runtimeProps.currentUser.id);
            query.append("_start", start.toString());
            query.append("_end", end.toString());

            try {
                setIsSubmissionLoading(true);
                const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + `/submissions/?${query.toString()}`);
                const total = parseInt(response.headers.get("X-Total-Count") || "0", 10);
                setTotalSubmissions(total);
            } catch (err) {
                console.error("Error fetching documents:", err);
            } finally {
                setIsSubmissionLoading(false);
            }
        }

        fetchSubmissions();
    }, [runtimeProps.currentUser]);

    const fetchAllMyPapers = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;

        try {
            const start = 1;
            const end = 2;
            const query = new URLSearchParams();

            query.append("user_id", runtimeProps.currentUser.id);
            query.append("_start", start.toString());
            query.append("_end", end.toString());

            const response1 = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL  + `/paper_owners/?${query.toString()}`);
            if (!response1.ok) {
                if (response1.status >= 500) {
                    showNotification("Data service is not responding", "warning");
                    return;
                }
                const message = await response1.text();
                showNotification(message, "warning");
                return;
            }
            const total = parseInt(response1.headers.get("X-Total-Count") || "0", 10);
            setAllPaperCount(total);
        } catch (err) {
            console.error("Error fetching documents:", err);
        }
        finally {
            setIsLoading(false);
        }
    }, [runtimeProps.currentUser]);

    useEffect(() => {
        fetchAllMyPapers();
    }, [fetchAllMyPapers]);

    const info = isLoading || isSubmissionLoading ? (<CircularProgress color="secondary" />) : (
        <ArticleInfo key="article-info" authorCount={totalSubmissions} ownerCount={allPaperCount} submitCount={0} />);
    return (info);
}

export default YourDocuments;
