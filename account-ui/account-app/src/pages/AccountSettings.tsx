import React, {useCallback, useContext, useState} from "react";
import {
    Container,
    Typography,
    Paper,
    Button,
    Link,
    Box,
    Checkbox, FormGroup, FormControlLabel, Tooltip
} from "@mui/material";
import { VerifiedUser, Edit, Lock, Email, Link as LinkIcon, Notifications as NofificationIcon } from "@mui/icons-material";

import {RuntimeContext, RuntimeProps} from "../RuntimeContext.tsx";
import PreflightChecklist from "../bits/PreflightChecklist.tsx";
import Authorship from "../bits/Authorship.tsx";
import YesNoDialog from "../bits/YesNoDialog.tsx";
import SubmissionsTable from "../bits/SubmissionsTable.tsx";


const VerifyEmailButton: React.FC<{ runtimeProps: RuntimeProps }> = ({ runtimeProps }) => {
    const user = runtimeProps.currentUser;
    const [dialogOpen, setDialogOpen] = useState(false);

    const verifyEmailRequest = useCallback(() => {
        async function requestEmail() {
            try {
                const reply = await fetch(`${runtimeProps.AAA_URL}/account/email/verify/`, {
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
    }, [user?.email, runtimeProps.AAA_URL]);
/*
         <Button variant="outlined" startIcon={<VerifiedUser />} href="/user/verify-email" disabled={user?.email_verified}>Send verification email</Button>

 */
    return (
        <>
            <Button
                variant="outlined"
                startIcon={<VerifiedUser />}
                disabled={user === null || user?.email_verified}
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


const AccountSettings = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    let url = user?.url || "https://arxiv.org";

    console.log(JSON.stringify(user));

    if (!url.startsWith("/")) {
        if (!url.startsWith("http")) {
            url = "https://" + url;
        }
    }

    const need_verify = user?.email_verified ? null : (
        <Tooltip title={"Please verify your email"}>
            <NofificationIcon />
        </Tooltip>
    );


    return (
        <Container maxWidth="md" sx={{ mt: 3 }}>
            <Paper elevation={3} sx={{ p: 3, width: "95%" }}>
                <Typography variant="h4" gutterBottom>
                    Your arXiv.org Account
                </Typography>
                <Box sx={{
                    backgroundColor: "#f2f2f8",
                    textAlign: "left",
                    py: 2,
                    mt: "auto",
                    display: "flex",
                    justifyContent: "space-between", // Ensures 4 boxes take equal space
                    px: 2, // Add padding to keep spacing
                }}>
                    <Box sx={{flex:1}}>
                        <Typography variant="body1"><b>{"E-mail: "}</b>
                            {user?.email}{need_verify}
                        </Typography>
                        <Typography variant="body1"><b>{"Name: "}</b>{user?.first_name}{", "}{user?.last_name}</Typography>
                        <Typography variant="body1"><b>{"Default Category: "}</b>{user?.default_category?.archive}.{user?.default_category?.subject_class}</Typography>
                        <Typography variant="body1"><b>{"Groups: "}</b>{user?.groups}</Typography>
                    </Box>
                    <Box sx={{flex:1}}>
                        <Typography variant="body1"><b>{"Affiliation: "}</b>{user?.affiliation}</Typography>
                        <Typography variant="body1"><b>{"URL: "}</b> <Link href={url} target="_blank">{user?.url}</Link></Typography>
                        <Typography variant="body1"><b>{"Country: "}</b>{user?.country}</Typography>
                        <Typography variant="body1"><b>{"Career Status: "}</b>{user?.career_status}</Typography>
                    </Box>
                </Box>
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <Button disabled={user === null}
                            variant="outlined" startIcon={<Edit />} href="/user/edit">Change User Information</Button>
                    <Button disabled={user === null}
                            variant="outlined" startIcon={<Lock />} href="/user/change_own_password">Change Password</Button>
                    <Button disabled={user === null}
                            variant="outlined" startIcon={<Email />} href="/user/change_email">Change Email</Button>
                    <VerifyEmailButton runtimeProps={runtimeProps} />
                </Box>
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <FormGroup>
                        <Tooltip title="MathJax is a javascript display engine for rendering TEX or MathML-coded mathematics in browsers without requiring font installation or browser plug-ins. Any modern browser with javascript enabled will be MathJax-ready. For general information about MathJax, visit mathjax.org.">
                            <FormControlLabel control={
                                <Checkbox defaultChecked
                                          disabled={user === null}
                                />
                            } label={(
                                <div>
                                    {"Enable MathJax "}
                                    <Link href={"https://info.arxiv.org/help/mathjax.html"}><LinkIcon/>Help</Link>
                                </div>
                            )} />
                        </Tooltip>
                    </FormGroup>
                </Box>
            </Paper>

            <Paper elevation={3} sx={{ p: 3, mt: 4, width: "95%" }}>
                <Typography variant="h5" gutterBottom>
                    Your Submissions
                </Typography>
                <SubmissionsTable runtimeProps={runtimeProps} />
                <Box sx={{ mt: 2 }}>
                    <Button
                        disabled={runtimeProps.currentUser === null}
                        variant="contained"
                        startIcon={<Edit />}
                        href="/submissions/"
                        sx={{
                            color: "white", // Default text color
                            "&:hover": {
                                color: "white", // Keep text white on hover
                            },
                        }}
                    >
                        Open Submission management
                    </Button>
                </Box>
            </Paper>

            <PreflightChecklist />
            <Authorship />
        </Container>
    );
};

export default AccountSettings;
