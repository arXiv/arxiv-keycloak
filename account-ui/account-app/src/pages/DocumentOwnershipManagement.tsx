import React from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import UserDocumentList from "../components/UserDocumentList.tsx";

const DocumentOwnershipManagement: React.FC = () => {
    return (
        <Container maxWidth={"md"}>
            <Box display="flex" flexDirection={"column"} sx={{my: "2em"}}>
                <Typography variant={"h1"}>
                    Manage Ownership
                </Typography>
                <UserDocumentList />
            </Box>
        </Container>
    );
}

export default DocumentOwnershipManagement;
