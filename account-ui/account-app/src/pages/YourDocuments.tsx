import React, {useCallback, useContext, useEffect, useState} from "react";
import CircularProgress from "@mui/material/CircularProgress";
import {useNotification} from "../NotificationContext";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import {RuntimeContext} from "../RuntimeContext";
import Link from "@mui/material/Link";
import {Link as RouterLink} from 'react-router-dom';
import AuthorInfoTable from "../bits/AuthorInfoTable";
import Typography from "@mui/material/Typography/Typography";
// import NavigateLink from "../bits/NavigateLink";
import {paths as adminApi} from "../types/admin-api";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import { ADMIN_USER_ID_DOCUMENT_SUMMARY_URL } from "../types/admin-url.ts";

type DocumentSummaryProps = adminApi[typeof ADMIN_USER_ID_DOCUMENT_SUMMARY_URL]['get']['responses']['200']['content']['application/json'];


const ArticleInfo: React.FC<DocumentSummaryProps & {isLoading: boolean}> = ({
                                                                                owns_count,
                                                                                submitted_count,
                                                                                authored_count,
                                                                                isLoading
                                                     }) => {
    const runtimeProps = useContext(RuntimeContext);
    return (
        <Container maxWidth={"md"}>
            <Box display="flex" flexDirection={"column"} sx={{my: "2em"}}>
                <Typography variant={"h1"}>
                    Your Articles
                </Typography>
                <CardWithTitle title={"Summary"}>
                    <Box sx={{py: 0}}>
                        {
                            isLoading ? (<CircularProgress color="secondary"/>) : (
                                <AuthorInfoTable ownerCount={owns_count} submitCount={submitted_count}
                                                 authorCount={authored_count}/>

                                )
                        }
                        <p>
                            {"Are you incorrectly registered as an author or a non-author of any articles you own? If so, update the authorship status "}
                            <Link component={RouterLink} to={"/user-account/owned-documents"}>
                                here.
                            </Link>
                        </p>

                        <Typography component="div" sx={{mt: 2}}>
                            Are there articles you are an author of on arXiv that are not listed here?
                            <ul style={{paddingLeft: '1.5em', marginTop: 0}}>
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
                                        the Request Authorship form
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

                    </Box>

                </CardWithTitle>
            </Box>
        </Container>
    );
};


const YourDocuments: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [documentSummary, setDocumentSummary] = useState<DocumentSummaryProps>({
        owns_count: 0, submitted_count: 0, authored_count: 0
    });
    const {showNotification} = useNotification();


    const fetchSummary = useCallback(async () => {
        if (!runtimeProps.currentUser)
            return;
        const user_id = runtimeProps.currentUser.id;
        try {
            setIsLoading(true);
            const getDocumentSummary = runtimeProps.adminFetcher.path(ADMIN_USER_ID_DOCUMENT_SUMMARY_URL).method('get').create();
            const response = await getDocumentSummary({user_id: Number(user_id)});
            
            if (response.ok) {
                const summary: DocumentSummaryProps = response.data;
                setDocumentSummary(summary);
            } else {
                if (response.status >= 500) {
                    showNotification("Data service is not responding", "warning");
                    return;
                }
                const errorMessage = (response.data as any)?.detail || response.statusText || "Error fetching document summary";
                showNotification(errorMessage, "warning");
            }
        } catch (err) {
            console.error("Error fetching document summary:", err);
        } finally {
            setIsLoading(false);
        }
    }, [runtimeProps.currentUser, runtimeProps.adminFetcher]);

    useEffect(() => {
        fetchSummary();
    }, [fetchSummary]);

    return (
        <ArticleInfo key="article-info" authored_count={documentSummary.authored_count} isLoading={isLoading}
                     owns_count={documentSummary.owns_count} submitted_count={documentSummary.submitted_count}/>
    );
}

export default YourDocuments;
