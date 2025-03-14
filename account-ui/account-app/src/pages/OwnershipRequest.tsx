import React, {useContext, useState} from "react";
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
import { useQuery } from "@tanstack/react-query";

import {RuntimeContext, RuntimeProps} from "../RuntimeContext.tsx";
// import YesNoDialog from "../bits/YesNoDialog.tsx";
import { paths as adminApi } from "../types/admin-api";

type ArxivDocument = adminApi['/v1/documents/paper_id/{paper_id}']['get']['responses']['200']['content']['application/json'];

/*
const SubmitRequest: React.FC<{ runtimeProps: RuntimeProps }> = ({ runtimeProps }) => {
    const user = runtimeProps.currentUser;
    const [dialogOpen, setDialogOpen] = useState(false);

    const verifyEmailRequest = useCallback(() => {
        async function requestEmail() {
            try {
                const reply = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/account/email/verify/`, {
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


// Define the shape of a row
interface TableRowData {
    id: string;
    middle: string;
    right: string;
}

// Function to fetch data based on ID
async function fetchData(id: string, runtimeProps: RuntimeProps) : Promise<TableRowData> {
    if (!id) return {id: "", middle : "", right: "" };
    try {
        const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/documents/paper_id/" + id);
        const doc: ArxivDocument = await response.json();
        return {id: doc.paper_id, middle: doc.title, right: doc.authors || ""};
    }
    catch (error) {
        return {id: "", middle : "", right: "" };
    }
}

const TableRowComponent: React.FC<{
    runtimeProps: RuntimeProps;
    row: TableRowData;
    index: number;
    onIdChange: (index: number, newId: string) => void;
    onRemove: () => void;
}> = ({ runtimeProps, row, index, onIdChange, onRemove }) => {
    const { data } = useQuery({
        queryKey: ["data", row.id],
        queryFn: () => fetchData(row.id, runtimeProps),
        enabled: !!row.id, // Fetch only when ID is entered
    });

    return (
        <TableRow>
            <TableCell>
                <TextField
                    value={row.id}
                    onChange={(e) => onIdChange(index, e.target.value)}
                    size="small"
                    sx={{width: "12em"}}
                />
            </TableCell>
            <TableCell>{data?.middle || ""}</TableCell>
            <TableCell>{data?.right || ""}</TableCell>
            <TableCell>
                <IconButton onClick={onRemove} color="error">
                    <Delete />
                </IconButton>
            </TableCell>
        </TableRow>
    );
};


function EditableTable({runtimeProps} : {runtimeProps: RuntimeProps}) : React.ReactNode {
    const [rows, setRows] = useState<TableRowData[]>([{ id: "", middle: "", right: "" }]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleIdChange = (index: number, newId: string) => {
        const updatedRows = [...rows];
        updatedRows[index].id = newId;
        setRows(updatedRows);
        setError(null);
    };

    const addRow = () => {
        setRows([...rows, { id: "", middle: "", right: "" }]);
    };

    const removeRow = (index: number) => {
        setRows(rows.filter((_, i) => i !== index));
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);

        const ids = rows.map((row) => row.id.trim()).filter((id) => id !== ""); // Remove empty IDs

        if (ids.length === 0) {
            setError("Please enter at least one ID before submitting.");
            setLoading(false);
            return;
        }

        try {
            const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/ownership/requests/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ ids }), // Sending only IDs in the request
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const result = await response.json();
            console.log("Success:", result);
            alert("Data submitted successfully!");
        } catch (error) {
            setError("Failed to submit data. Please try again.");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const inputs = rows.map((row) => row.id.trim()).filter((value) => value !== "");

    return (
        <>
        <TableContainer component={Paper} sx={{ maxWidth: 800, margin: "auto", mt: 4 }}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Paper ID</TableCell>
                        <TableCell>Title</TableCell>
                        <TableCell>Authors</TableCell>
                        <TableCell>Actions</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {rows.map((row, index) => (
                        <TableRowComponent
                            runtimeProps={runtimeProps}
                            key={index}
                            row={row}
                            index={index}
                            onIdChange={handleIdChange}
                            onRemove={() => removeRow(index)}
                        />
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
            <Box sx={{ mt: 2, display: "flex", flexDirection: "row", alignItems: "center" }}>
                <Button onClick={addRow} startIcon={<Add />} variant="contained">
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
        <Container maxWidth="md" sx={{ mt: 3 }}>
            <Paper elevation={3} sx={{ p: 3, mt: 4, width: "95%" }}>
                <Typography variant="h5" gutterBottom>
                    Ownership Request
                </Typography>
                <EditableTable runtimeProps={runtimeProps} />
            </Paper>

        </Container>
    );
};

export default OwnershipRequest;
