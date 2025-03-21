import React, {ChangeEvent, useContext, useEffect, useState} from "react";
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
type PaperOwnerRequestType = adminApi['/v1/paper_owners/authorize']['post']['requestBody']['content']['application/json'];

import {printUserName} from "../bits/printer.ts";
import {useNotification} from "../NotificationContext.tsx";
import {useFetchPlus} from "../fetchPlus.ts";


const ClaimPaperOwnership: React.FC = () => {
    const {showNotification, showMessageDialog} = useNotification();
    const [inProgress, setInProgress] = useState(false);
    const runtimeProps = useContext(RuntimeContext);
    const [formData, setFormData] = useState<PaperOwnerRequestType>({user_id: runtimeProps.currentUser?.id || "", paper_id: "", password: "", verify_id: false});
    const [document, setDocument] = useState<DocumentType|null>(null);
    const fetchPlus = useFetchPlus();

    useEffect(() => {
        async function fetchDocument() {
            if (runtimeProps.currentUser && formData.paper_id) {
                try {
                    setInProgress(true);
                    const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + "/documents/paper_id/" + formData.paper_id);
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
    }, [runtimeProps.currentUser, formData.paper_id]);


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        setInProgress(true);

        event.preventDefault();

        try {
            const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + "/paper_owners/authorize/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (response.status === 201) {
                showMessageDialog(document?.title || formData.paper_id, "You claimed successfully!");
            }
            else {
                const reply = await response.json();
                if (response.status >= 500) {
                    showNotification("Server is not responding", "error");
                }
                else if (response.status === 409) {
                    showMessageDialog(reply.detail, "You have the ownership");
                }
                else if (response.status === 403) {
                    showMessageDialog(reply.detail, "It is forbidden");
                }
                else if (response.status === 400) {
                    showMessageDialog(reply.detail, "Incorrect input");
                }
                else {
                    showMessageDialog(reply.detail, `Unexpected error (${response.status})`);
                }
            }

        }
        catch (error) {
            console.log(error);
            showNotification(String(error), "error");
        }
        finally {
            setInProgress(false);
        }
    };

    const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
        if (!runtimeProps.currentUser) {
            showNotification("Please log in.", "warning");
            return;
        }

        const value = event.target.value;
        const name = event.target.name;
        setFormData({...formData, [name]: value});
    }

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
                        value={formData.paper_id}
                        onChange={handleChange}
                        sx={{width: "120px", flexShrink: 0}}
                        helperText={document ? "Valid ID" : "Invalid ID"}
                    />
                    <Typography sx={{flex: 1}} variant="body2">{document ? `${document.title} by ${document.authors}` : "e.g. 1003.7623 or hep-th/0207099"}</Typography>
                </Box>
                <Box sx={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 1 }}>
                <TextField
                    id="password"
                    name="password"
                    label="Paper Password"
                    variant="outlined"
                    value={formData.password}
                    onChange={handleChange}
                    sx={{width: "120px", flexShrink: 0}}
                    helperText=""
                />
                    <Typography sx={{flex: 1}} variant="body2">e.g. juq87"</Typography>
                </Box>
                <FormControlLabel
                    control={<Checkbox checked={formData.verify_id} onChange={(e) => setFormData(
                        {...formData, verify_id: e.target.checked})} />}
                    label={
                        <span>
              I certify that my name is <b>{printUserName(runtimeProps.currentUser)}</b>, my username is <b>{runtimeProps.currentUser?.username}</b> (<a href="#">Click here</a> if you are not), and my email address is <b>{runtimeProps.currentUser?.email}</b> (<a href="#">Click here</a> if your email address has changed.)
            </span>
                    }
                />
                <Button type="submit" variant="contained" color="primary" disabled={inProgress || !formData.verify_id || !runtimeProps.currentUser}>
                    Submit
                </Button>
            </Box>
            </CardContent>
            </Card>
        </Container>
    );
};

export default ClaimPaperOwnership;