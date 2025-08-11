import React, {useContext, useState, useEffect} from "react";
import Typography from "@mui/material/Typography";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import Paper from "@mui/material/Paper";
import Container from "@mui/material/Container";
import IconButton from "@mui/material/IconButton";
import TextField from "@mui/material/TextField";

import { Add, Delete } from "@mui/icons-material";

import {RuntimeContext, RuntimeProps} from "../RuntimeContext.tsx";
// import YesNoDialog from "../bits/YesNoDialog.tsx";
import { paths as adminApi } from "../types/admin-api";
import {useNotification} from "../NotificationContext.tsx";
import {utcToNnewYorkDatePrinter} from "../bits/printer.ts";
import YourOwnershipRequests from "../components/YourOwnershipRequests.tsx";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import {ADMIN_DOCUMENT_PAPER_ID_UPL, ADMIN_OWNERSHIP_REQUESTS_URL} from "../types/admin-url.ts";

type ArxivDocument = adminApi[typeof  ADMIN_DOCUMENT_PAPER_ID_UPL]['get']['responses']['200']['content']['application/json'];

type OwnershipRequestsRequest = adminApi[typeof ADMIN_OWNERSHIP_REQUESTS_URL]['post']['requestBody']['content']['application/json'];



/*
const SubmitRequest: React.FC<{ runtimeProps: RuntimeProps }> = ({ runtimeProps }) => {
    const user = runtimeProps.currentUser;
    const [dialogOpen, setDialogOpen] = useState(false);

    const verifyEmailRequest = useCallback(() => {
        async function requestEmail() {
            try {
                const reply = await fetchPlus(`${runtimeProps.ADMIN_API_BACKEND_URL}/account/email/verify/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email: user?.email }), // Convert object to JSON string
                });

                if (!reply.ok) {
                    console.error("Failed to send verification email", reply.status, await reply.text());
                } else {
                    console.log("Verification email sent successfully!");
                }
            } catch (error) {
                console.error("Error sending verification email", error);
            }
        }
        requestEmail();
        setDialogOpen(false); // Close dialog after sending request
    }, [user?.email, runtimeProps.ADMIN_API_BACKEND_URL]);

    //          <Button variant="outlined" startIcon={<VerifiedUser />} href="/user-account/verify-email" disabled={user?.email_verified}>Send verification email</Button>

    return (
        <>
            <Button
                variant="outlined"
                disabled={user?.email_verified}
                onClick={() => setDialogOpen(true)} // Open dialog when clicked
            >
                Send verification email
            </Button>

            <YesNoDialog
                title={"Request Verification email"}
                message={`Resend verification email to ${user?.email} ?`}
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
                onConfirm={verifyEmailRequest}
            />
        </>
    );
};
*/



const OwnershipRequestTableRowComponent: React.FC<{
    runtimeProps: RuntimeProps;
    paperId: string;
    index: number;
    onIdChange: (index: number, newId: string) => void;
    onRemove: () => void;
}> = ({ runtimeProps, paperId, index, onIdChange, onRemove }) => {

    const [document, setDocument] = useState<ArxivDocument | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchPaperData = async () => {
            if (!paperId) {
                setDocument(null);
                setError(null);
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const getDocument = runtimeProps.adminFetcher.path(ADMIN_DOCUMENT_PAPER_ID_UPL).method('get').create();
                const response = await getDocument({paper_id: paperId});
                
                if (response.ok) {
                    const doc: ArxivDocument = response.data;
                    setDocument(doc);
                } else if (response.status === 404) {
                    setDocument(null);
                    setError(`${paperId}: Invalid paper ID`);
                } else {
                    const errorMessage = (response.data as any)?.detail || response.statusText || "Error fetching document";
                    setDocument(null);
                    setError(errorMessage);
                }
            } catch (error: any) {
                console.error("Error fetching paper data:", error);
                setDocument(null);
                setError("Error fetching document");
            } finally {
                setLoading(false);
            }
        };

        fetchPaperData();
    }, [paperId, runtimeProps]);

    return (
        <TableRow>
            <TableCell>
                <TextField
                    value={paperId}
                    onChange={(e) => onIdChange(index, e.target.value)}
                    size="small"
                    sx={{width: "12em"}}
                />
            </TableCell>
            <TableCell>{document ? utcToNnewYorkDatePrinter(document.dated) : ""}</TableCell>
            <TableCell>{loading ? "Loading..." : (error || document?.title || "")}</TableCell>
            <TableCell>{document?.authors || ""}</TableCell>
            <TableCell>
                <IconButton onClick={onRemove} color="error">
                    <Delete />
                </IconButton>
            </TableCell>
        </TableRow>
    );
};

function OwnershipRequestTable({runtimeProps} : {runtimeProps: RuntimeProps}) : React.ReactNode {
    const {showNotification, showMessageDialog} = useNotification();
    const [paperIds, setPaperIds] = useState<string[]>([""]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleIdChange = (index: number, newId: string) => {
        const updatedIds = [...paperIds];
        updatedIds[index] = newId;
        setPaperIds(updatedIds);
        console.log(JSON.stringify(updatedIds));
        setError(null);
    };

    const addRow = () => {
        setPaperIds([...paperIds, ""]);
    };

    const removeRow = (index: number) => {
        setPaperIds(paperIds.filter((_, i) => i !== index));
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);

        const ids = paperIds.map((id) => id.trim()).filter((id) => id !== ""); // Remove empty IDs
        const body: OwnershipRequestsRequest = {
            user_id: runtimeProps.currentUser?.id ? String(runtimeProps.currentUser.id) : undefined,
            arxiv_ids: ids,
        };

        if (ids.length === 0) {
            setError("Please enter at least one ID before submitting.");
            setLoading(false);
            return;
        }

        try {
            const postOwnershipRequest = runtimeProps.adminFetcher.path(ADMIN_OWNERSHIP_REQUESTS_URL).method('post').create();
            const response = await postOwnershipRequest(body);

            if (!response.ok) {
                const errorMessage = (response.data as any)?.detail || response.statusText || "Error submitting request";
                showNotification(`Error: ${errorMessage}`, "error");
                return;
            }

            // const result = response.data;
            showMessageDialog("", "Request submitted successfully!")
        } catch (error) {
            showNotification("Failed to submit data. Please try again.", "error");
            setError("Failed to submit data. Please try again.");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const inputs = paperIds.map((id) => id.trim()).filter((value) => value !== "");

    return (
        <>
        <TableContainer component={Paper} sx={{ maxWidth: 800, margin: "auto", mt: 4 }}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Paper ID</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell>Title</TableCell>
                        <TableCell>Authors</TableCell>
                        <TableCell>Actions</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {paperIds.map((paperId, index) => (
                        <OwnershipRequestTableRowComponent
                            runtimeProps={runtimeProps}
                            key={index}
                            paperId={paperId}
                            index={index}
                            onIdChange={handleIdChange}
                            onRemove={() => removeRow(index)}
                        />
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
            <Box sx={{ mt: 2, display: "flex", flexDirection: "row", alignItems: "center" }}>
                <Button onClick={addRow} startIcon={<Add />} variant="outlined">
                  Add Row
               </Button>

                <Box sx={{flexGrow: 1}}/>
                {error && <Box sx={{ color: "red", textAlign: "center", mt: 2 }}>{error}</Box>}

                <Button onClick={handleSubmit} variant="contained" color="primary" disabled={loading || inputs.length === 0} >
                    {loading ? "Submitting..." : "Submit"}
                </Button>
            </Box>
        </>
    );
}


const OwnershipRequest = () => {
    const runtimeProps: RuntimeProps = useContext(RuntimeContext);

    return (
        <Container maxWidth={"md"} sx={{gap: "2em"}}>
            <Box display="flex" flexDirection={"column"} sx={{my: "4em", gap: "2em"}}>
                <Typography variant={"h1"}>
                    Ownership Requests
                </Typography>

                <CardWithTitle title={"Submit Request"}>
                    <Typography variant={"body1"}>
                        To process an ownership request, enter either the numeric request id.
                    </Typography>
                    <OwnershipRequestTable runtimeProps={runtimeProps} />
                    <Typography variant={"body2"} sx={{fontWeight: "bold", mt: 2}}>
                        {"If you have a large number of paper IDs to request, please contact "}
                        {runtimeProps.URLS.arxivAdminContactEmail}
                    </Typography>
                </CardWithTitle>
            </Box>

            <YourOwnershipRequests runtimeProps={runtimeProps} />
        </Container>
    );
};

export default OwnershipRequest;
