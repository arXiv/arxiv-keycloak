import React, {useCallback, useContext, useEffect, useState} from "react";
import Container from '@mui/material/Container'
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Paper  from "@mui/material/Paper";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
// import Checkbox from "@mui/material/Checkbox";
import FormGroup from "@mui/material/FormGroup";
import Tooltip from "@mui/material/Tooltip";

import VerifiedUser from "@mui/icons-material/VerifiedUser";
import Edit from "@mui/icons-material/Edit";
import Email from "@mui/icons-material/Email";
import PasswordIcon from "@mui/icons-material/Password";
import WarningIcon from "@mui/icons-material/Warning";
// import LinkIcon from "@mui/icons-material/Link";
import NofificationIcon from "@mui/icons-material/Notifications";
import AdminIcon from "@mui/icons-material/Check";
import ModIcon from "@mui/icons-material/People";
import CanLockIcon from "@mui/icons-material/Lock";
import SystemIcon from "@mui/icons-material/Settings";

import {RuntimeContext, RuntimeProps} from "../RuntimeContext.tsx";
import PreflightChecklist from "../bits/PreflightChecklist.tsx";
import YesNoDialog from "../bits/YesNoDialog.tsx";
// import SubmissionsTable from "../bits/SubmissionsTable.tsx";
import YourSubmissions from "../components/YourSubmissions.tsx";
import {useNotification} from "../NotificationContext.tsx";

import { paths as adminApi } from "../types/admin-api";
import MathJaxToggle from "../bits/MathJaxToggle.tsx";
import {fetchPlus} from "../fetchPlus.ts";
import EndorsedCategories from "../bits/EndorsedCategories.tsx";
import {useNavigate} from "react-router-dom";

type EndorsementListType = adminApi["/v1/endorsements/"]["get"]['responses']["200"]['content']['application/json'];


const VerifyEmailButton: React.FC<{ runtimeProps: RuntimeProps }> = ({ runtimeProps }) => {
    const user = runtimeProps.currentUser;
    const [dialogOpen, setDialogOpen] = useState(false);

    const verifyEmailRequest = useCallback(() => {
        async function requestEmail() {
            try {
                const reply = await fetchPlus(`${runtimeProps.AAA_URL}/account/email/verify/`, {
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
         <Button variant="outlined" startIcon={<VerifiedUser />} href="/user-account/verify-email" disabled={user?.email_verified}>Send verification email</Button>

 */
    return (
        <>
            <Button
                variant="outlined"
                startIcon={<VerifiedUser />}
                disabled={user === undefined || user === null || user.email_verified === true}
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


const UserAccountInfo = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const {showMessageDialog} = useNotification();
    const [endorsements, setEndorsements] = useState<EndorsementListType>([]);
    const navigate = useNavigate();

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

    useEffect(() => {
        if (runtimeProps.updateCurrentUser)
            runtimeProps.updateCurrentUser();
    }, []) ;


    useEffect(() => {
        async function doGetEndorsedCategories() {
            if (!runtimeProps.currentUser) return;
            const query = new URLSearchParams();
            query.set("endorsee_id", runtimeProps.currentUser.id);
            query.set("type", "user");
            try {
                const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + `/endorsements/?${query.toString()}`);
                const body: EndorsementListType = await response.json();
                setEndorsements(body);
            }
            catch (error) {
                console.error(error);
            }
        }

        if (runtimeProps.currentUser)
            doGetEndorsedCategories()
        if (runtimeProps.currentUser)
            doGetEndorsedCategories()
        else
            showMessageDialog("You are not logged in to use see your account.", "Please log in");
    }, [runtimeProps.currentUser]);

    const vetoStatus= runtimeProps.currentUser?.veto_status && runtimeProps.currentUser?.veto_status !== "ok" ? (
        <Typography variant="body1" component="div"><b>{"Account Status: "} </b>
            {runtimeProps.currentUser?.veto_status === "no-endorse" ? (
                <Tooltip slotProps={{tooltip: {sx: {fontSize: "1.2em"}} }}
                         title={"You may not endorse other users."}>
                    <span>
                        <WarningIcon />
                        <Typography variant="body1" component="span">
                            No Endorse
                        </Typography>
                    </span>
                </Tooltip>
                ) : null}
            {runtimeProps.currentUser?.veto_status === "no-upload" ? (
                <Tooltip slotProps={{tooltip: {sx: {fontSize: "1.2em"}} }}
                         title={"Your ability to submit papers to arXiv has been suspended by administrative action. Contact moderation@arxiv.org for more information."}>
                    <span>
                        <WarningIcon />
                        <Typography variant="body1" component="span">No Upload</Typography>
                    </span>
                </Tooltip>
            ) : null}
            {runtimeProps.currentUser?.veto_status === "no-replace" ? (
                <Tooltip slotProps={{tooltip: {sx: {fontSize: "1.2em"}} }}
                         title={"Your ability to submit papers to arXiv has been suspended by administrative action. Contact moderation@arxiv.org for more information."}>
                    <span>
                        <WarningIcon />
                        <Typography variant="body1" component="span">Replace</Typography>
                    </span>
                </Tooltip>
            ) : null}
        </Typography>
    ) : null;

    const roles = runtimeProps.isAdmin || runtimeProps.isMod || runtimeProps.isCanLock || runtimeProps.isSystem ? (
        <Typography variant="body1"><b>{"Role: "} </b>
            {runtimeProps.isMod ?  <Tooltip title="Moderator" children={<ModIcon />} /> : null}
            {runtimeProps.isAdmin ? <Tooltip title="Administrator" children={<AdminIcon />} /> : null}
            {runtimeProps.isSystem ? <Tooltip title="Sysadmin staff" children={<SystemIcon />} /> : null}
            {runtimeProps.isCanLock ? <Tooltip title="Can Lock" children={<CanLockIcon />} /> : null}
        </Typography>
    ) : null;

    const endorsedCategories = endorsements ? <EndorsedCategories endorsements={endorsements} key={user?.id || "user"} runtimeProps={runtimeProps} /> : null;


    return (
        <Container maxWidth={"md"} sx={{ mt: 0 }}>
            <Paper elevation={3} sx={{ p: 3}}>
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
                        <Typography variant="body1"><b>{"Name: "}</b>{user?.first_name}{", "}{user?.last_name}</Typography>
                        <Typography variant="body1"><b>{"User name: "}</b>{user?.username}</Typography>
                        <Typography variant="body1"><b>{"E-mail: "}</b>{user?.email}{need_verify}</Typography>
                        <Typography variant="body1"><b>{"Default Category: "}</b>{user?.default_category?.archive}.{user?.default_category?.subject_class}</Typography>
                        <Typography variant="body1"><b>{"Groups: "}</b>{user?.groups}</Typography>
                        <Typography variant="body1" component="div"><b>{"Endorsed categories: "}</b>{endorsedCategories}</Typography>
                    </Box>
                    <Box sx={{flex:1}}>
                        {vetoStatus}
                        {roles}
                        <Typography variant="body1"><b>{"Affiliation: "}</b>{user?.affiliation}</Typography>
                        <Typography variant="body1"><b>{"URL: "}</b> <Link href={url} target="_blank">{user?.url}</Link></Typography>
                        <Typography variant="body1"><b>{"Country: "}</b>{user?.country}</Typography>
                        <Typography variant="body1"><b>{"Career Status: "}</b>{user?.career_status}</Typography>
                    </Box>
                </Box>
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <Button component="a" disabled={user === null}
                            variant="outlined" startIcon={<Edit />} onClick={() => navigate(runtimeProps.URLS.userChangeProfile)}>Change User Information</Button>
                    <Button disabled={user === null}
                            variant="outlined" startIcon={<PasswordIcon />} onClick={ () => navigate(runtimeProps.URLS.userChangePassword)}>Change Password</Button>
                    <Button disabled={user === null}
                            variant="outlined" startIcon={<Email />} onClick={() => navigate(runtimeProps.URLS.userChangeEmail)}>Change Email</Button>
                    <VerifyEmailButton runtimeProps={runtimeProps} />
                </Box>
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <FormGroup>
                        <MathJaxToggle />
                    </FormGroup>
                </Box>
            </Paper>

            <YourSubmissions runtimeProps={runtimeProps} />

            <PreflightChecklist runtimeProps={runtimeProps} />
        </Container>
    );
};

export default UserAccountInfo;
