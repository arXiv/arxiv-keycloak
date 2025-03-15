import React, {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";

import {RuntimeContext} from "../RuntimeContext";
// import {useNotification} from "../NotificationContext";

import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";

// import FormControl from "@mui/material/FormControl";
// import Link from "@mui/material/Link";
import {paths as adminApi} from "../types/admin-api";
type DocumentType = adminApi['/v1/documents/paper_id/{paper_id}']['get']['responses']['200']['content']['application/json'];

import {printUserName} from "../bits/printer.ts";
import {useNotification} from "../NotificationContext.tsx";

const ClaimPaperOwnership: React.FC = () => {
    const {showNotification, showMessageDialog} = useNotification();
    const [inProgress, setInProgress] = useState(false);
    const runtimeProps = useContext(RuntimeContext);
    const [formData, setFormData] = useState<{paperId: string, password: string, verifyId: boolean}>({paperId: "", password: "", verifyId: false});
    const [document, setDocument] = useState<DocumentType|null>(null);

    useEffect(() => {
        async function fetchDocument() {
            if (runtimeProps.currentUser && formData.paperId) {
                try {
                    setInProgress(true);
                    const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/documents/paper_id/" + formData.paperId);
                    if (response.ok) {
                        const doc = await response.json();
                        setDocument(doc);
                    }
                    else {
                        setDocument(null);
                        if (response.status >= 500) {
                            showNotification("Server is not responding", "error");
                        }
                    }
                }
                catch (error) {

                }
                finally {
                    setInProgress(false);
                }
            }
        }

        fetchDocument();
    }, [runtimeProps.currentUser, formData.paperId]);


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        setInProgress(true);

        event.preventDefault();

        try {
            const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/document/claim", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });
            if (response.ok) {
                showMessageDialog(document?.title || formData.paperId, "You claimed successfully!");
            }
        }
        catch (error) {

        }
        finally {
            setInProgress(false);
        }
    };

    return (
        <Container maxWidth="sm">
            <Card>
                <CardHeader title="Claim Ownership: Enter Paper ID and Password" />
                <CardContent>

            <Typography >
                By entering the paper ID and <i>paper password</i> associated with a paper, you can become registered as the <i>owner</i> of a paper.
            </Typography>
            <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Box sx={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 1 }}>
                    <TextField
                        id="paper_id"
                        name="paper_id"
                        label="Paper ID"
                        variant="outlined"
                        value={formData.paperId}
                        onChange={(e) => setFormData({
                            ...formData,
                            paperId: e.target.value,
                        })}
                        sx={{width: "120px", flexShrink: 0}}
                        helperText={document ? "Valid ID" : "Invalid ID"}
                    />
                    <Typography sx={{flex: 1}} variant="body2">{document ? `${document.title} by ${document.authors}` : "e.g. 1003.7623 or hep-th/0207099"}</Typography>
                </Box>
                <Box sx={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 1 }}>
                <TextField
                    id="paper_password"
                    name="paper_password"
                    label="Paper Password"
                    variant="outlined"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({
                        ...formData,
                        password: e.target.value,
                    })}
                    sx={{width: "120px", flexShrink: 0}}
                    helperText=""
                />
                    <Typography sx={{flex: 1}} variant="body2">e.g. juq87"</Typography>
                </Box>
                <FormControlLabel
                    control={<Checkbox checked={formData.verifyId} onChange={(e) => setFormData(
                        {...formData, verifyId: e.target.checked})} />}
                    label={
                        <span>
              I certify that my name is <b>{printUserName(runtimeProps.currentUser)}</b>, my username is <b>{runtimeProps.currentUser?.username}</b> (<a href="#">Click here</a> if you are not), and my email address is <b>{runtimeProps.currentUser?.email}</b> (<a href="#">Click here</a> if your email address has changed.)
            </span>
                    }
                />
                <Button type="submit" variant="contained" color="primary" disabled={inProgress || !formData.verifyId}>
                    Submit
                </Button>
            </Box>
            </CardContent>
            </Card>
        </Container>
    );
};

export default ClaimPaperOwnership;