import React, {useCallback, useContext, useEffect, useState} from "react";
import Container from '@mui/material/Container'
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
// import Checkbox from "@mui/material/Checkbox";
import FormGroup from "@mui/material/FormGroup";
import Tooltip from "@mui/material/Tooltip";

import VerifiedUser from "@mui/icons-material/VerifiedUser";
import Edit from "@mui/icons-material/Edit";
import Email from "@mui/icons-material/Email";
import PasswordIcon from "@mui/icons-material/Password";
// import WarningIcon from "@mui/icons-material/Warning";
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

import {paths as adminApi} from "../types/admin-api";
import MathJaxToggle from "../bits/MathJaxToggle.tsx";
import EndorsedCategories from "../bits/EndorsedCategories.tsx";
import {useNavigate} from "react-router-dom";
import CategoryGroup from "../bits/CategoryGroup.tsx";
import CountryName from "../bits/CountryName.tsx";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import {ADMIN_ENDORSEMENTS_URL} from "../types/admin-url.ts";
import {ACCOUNT_USER_EMAIL_VERIFY_URL} from "../types/aaa-url.ts";

type EndorsementListType = adminApi[typeof ADMIN_ENDORSEMENTS_URL]["get"]['responses']["200"]['content']['application/json'];


const VerifyEmailButton: React.FC<{ runtimeProps: RuntimeProps }> = ({runtimeProps}) => {
    const user = runtimeProps.currentUser;
    const [dialogOpen, setDialogOpen] = useState(false);

    const verifyEmailRequest = useCallback(() => {
        async function requestEmail() {
            if (!user?.id) return;
            try {
                const postEmailVerify = runtimeProps.aaaFetcher.path(ACCOUNT_USER_EMAIL_VERIFY_URL).method('post').create();
                const reply = await postEmailVerify({user_id: user.id, email: user?.email || ''});

                if (!reply.ok) {
                    console.error("Failed to send verification email", reply.status, reply.statusText);
                } else {
                    console.log("Verification email sent successfully!");
                }
            } catch (error) {
                console.error("Error sending verification email", error);
            }
        }

        requestEmail();
        setDialogOpen(false); // Close dialog after sending request
    }, [user?.email, user?.id, runtimeProps.aaaFetcher]);
    /*
             <Button variant="outlined" startIcon={<VerifiedUser />} href="/user-account/verify-email" disabled={user?.email_verified}>Send verification email</Button>

     */
    return (
        <>
            <Button
                variant="outlined"
                startIcon={<VerifiedUser/>}
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
    // const [demographic, setDemographic] = useState<DemographicType | null>(null);

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
            <NofificationIcon/>
        </Tooltip>
    );

    useEffect(() => {
        if (runtimeProps.updateCurrentUser)
            runtimeProps.updateCurrentUser();
    }, []);


    useEffect(() => {
        if (!runtimeProps.currentUser)
            showMessageDialog("Please log in first", "No user", () => <Link href={"/login"}/>);
    }, [runtimeProps.currentUser]);


    useEffect(() => {
        async function doGetEndorsedCategories() {
            if (!runtimeProps.currentUser?.id) return;
            try {
                const getEndorsements = runtimeProps.adminFetcher.path(ADMIN_ENDORSEMENTS_URL).method('get').create();
                const response = await getEndorsements({
                    endorsee_id: Number(runtimeProps.currentUser.id),
                    type: "user"
                });
                const body: EndorsementListType = response.data;
                setEndorsements(body);
            } catch (error) {
                console.error(error);
            }
        }

        if (runtimeProps.currentUser)
            doGetEndorsedCategories()
    }, [runtimeProps.currentUser]);

    /*
    useEffect(() => {
        async function doGetDemographic() {
            if (!runtimeProps.currentUser) return;
            try {
                const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + `/v1/demographics/${runtimeProps.currentUser.id}/`);
                const body: DemographicType = await response.json();
                setDemographic(body);
            }
            catch (error) {
                console.error(error);
            }
        }

        if (runtimeProps.currentUser)
            doGetDemographic()
    }, [runtimeProps.currentUser]);
    */

    const vetoed = !!(runtimeProps.currentUser?.veto_status && runtimeProps.currentUser?.veto_status !== "ok");
    /*
    const vetoStatus = vetoed ? (
        <Typography variant="body1" component="div"><b>{"Account Status: "} </b>
            {runtimeProps.currentUser?.veto_status === "no-endorse" ? (
                <Tooltip slotProps={{tooltip: {sx: {fontSize: "1.2em"}}}}
                         title={"You may not endorse other users."}>
                    <span>
                        <WarningIcon/>
                        <Typography variant="body1" component="span">
                            No Endorse
                        </Typography>
                    </span>
                </Tooltip>
            ) : null}
            {runtimeProps.currentUser?.veto_status === "no-upload" ? (
                <Tooltip slotProps={{tooltip: {sx: {fontSize: "1.2em"}}}}
                         title={vetoedMessage}>
                    <span>
                        <WarningIcon/>
                        <Typography variant="body1" component="span">No Upload</Typography>
                    </span>
                </Tooltip>
            ) : null}
            {runtimeProps.currentUser?.veto_status === "no-replace" ? (
                <Tooltip slotProps={{tooltip: {sx: {fontSize: "1.2em"}}}}
                         title={vetoedMessage}>
                    <span>
                        <WarningIcon/>
                        <Typography variant="body1" component="span">Replace</Typography>
                    </span>
                </Tooltip>
            ) : null}
        </Typography>
    ) : null;
    */

    const roles = runtimeProps.isAdmin || runtimeProps.isMod || runtimeProps.isCanLock || runtimeProps.isSystem ? (
        <Typography variant="body1"><b>{"Role: "} </b>
           {runtimeProps.isMod ? <Tooltip title="Moderator" children={<ModIcon/>}/> : null}
            {runtimeProps.isAdmin ? <Tooltip title="Administrator" children={<AdminIcon/>}/> : null}
            {runtimeProps.isSystem ? <Tooltip title="Sysadmin staff" children={<SystemIcon/>}/> : null}
            {runtimeProps.isCanLock ? <Tooltip title="Can Lock" children={<CanLockIcon/>}/> : null}
        </Typography>
    ) : null;

    const endorsedCategories = endorsements ?
        <EndorsedCategories endorsements={endorsements} key={user?.id || "user"} runtimeProps={runtimeProps}/> : null;

    const orcidId = runtimeProps.currentUser?.orcid_id;
    const orcidAuth = runtimeProps.currentUser?.orcid_authenticated;

    const orcidText = runtimeProps.currentUser?.orcid_id ? null : (
        <Typography>
            {"You are encouraged to associate your "}
            <a href="https://info.arxiv.org/help/orcid">ORCID</a>
            {" with your arXiv account. ORCID iDs are standard, persistent identifiers for research authors."}
            {orcidId && !orcidAuth ? (
                <>
                    Our search indicates that you may already have an
                    <a href="https://info.arxiv.org/help/orcid"> ORCID</a>:
                    <a href={`https://arxiv.org/a/${orcidId}`}> {orcidId}</a>. If this is the wrong iD, you may
                    change it below.
                </>
            ) : null}
            {"ORCID iDs will gradually supersede the role of the arXiv "}
            <a href="https://info.arxiv.org/help/author_identifiers">
                author identifier
            </a>
            {". To associate your ORCID iD with your arXiv account, please "}
            <a href="/user/confirm_orcid_id">
                confirm {orcidId && !orcidAuth ? "or correct" : ""} your ORCID iD
            </a>
            .
        </Typography>
    );

    return (
        <Container maxWidth={"md"} sx={{my: "4em", gap: 2}}>
            <Box display={"flex"} flexDirection={"column"} sx={{gap: "2em"}} >
            <Typography variant={"h1"} >Welcome to arXiv</Typography>
            <CardWithTitle title="Your Account Information">
                <Box sx={{
                    backgroundColor: "#f2f2f8",
                    textAlign: "left",
                    py: 2,
                    mt: "auto",
                    display: "flex",
                    justifyContent: "space-between", // Ensures 4 boxes take equal space
                    px: 2, // Add padding to keep spacing
                }}>
                    <Box sx={{flex: 1}}>
                        <Typography variant="body1"><b>{"Name: "}</b>{user?.first_name}{", "}{user?.last_name}
                        </Typography>
                        <Typography variant="body1"><b>{"User name: "}</b>{user?.username}</Typography>
                        <Typography variant="body1"><b>{"E-mail: "}</b>{user?.email}{need_verify}</Typography>
                        <Typography
                            variant="body1"><b>{"Default Category: "}</b>{user?.default_category?.archive}.{user?.default_category?.subject_class}
                        </Typography>
                        <Typography variant="body1" component="div"><b>{"Groups: "}</b>
                                {user?.groups?.map((group) => (
                                    <CategoryGroup key={group} groupId={group} component="span" />
                                ))}
                        </Typography>
                        <Typography variant="body1" component="div"><b>{"Endorsed categories: "}</b>{endorsedCategories}
                        </Typography>
                    </Box>
                    <Box sx={{flex: 1}}>
                        {/* vetoStatus */}
                        {roles}
                        <Typography variant="body1"><b>{"Affiliation: "}</b>{user?.affiliation}</Typography>
                        <Typography variant="body1"><b>{"URL: "}</b> <Link href={url} target="_blank">{user?.url}</Link></Typography>
                        <Typography variant="body1"><b>{"Country: "}</b><CountryName countryId={user?.country || ""} component="span" /></Typography>
                        <Typography variant="body1"><b>{"Career Status: "}</b>{user?.career_status}</Typography>
                        <Typography variant="body1"><b>{"ORCID: "}</b>{user?.orcid_id}</Typography>
                        <Typography variant="body1"><b>{"arXiv author ID: "}</b>{user?.author_id}</Typography>
                    </Box>
                </Box>
                {orcidText}
                <Box sx={{mt: 2, display: 'flex', gap: 2}}>
                    <Button component="a" disabled={user === null}
                            variant="outlined" startIcon={<Edit/>}
                            onClick={() => navigate(runtimeProps.URLS.userChangeProfile)}>Change User
                        Information</Button>
                    <Button disabled={user === null}
                            variant="outlined" startIcon={<PasswordIcon/>}
                            onClick={() => navigate(runtimeProps.URLS.userChangePassword)}>Change Password</Button>
                    <Button disabled={user === null}
                            variant="outlined" startIcon={<Email/>}
                            onClick={() => navigate(runtimeProps.URLS.userChangeEmail)}>Change Email</Button>
                    <VerifyEmailButton runtimeProps={runtimeProps}/>
                </Box>
                <Box sx={{mt: 2, display: 'flex', gap: 2}}>
                    <FormGroup>
                        <MathJaxToggle/>
                    </FormGroup>
                </Box>
            </CardWithTitle>

            <YourSubmissions runtimeProps={runtimeProps} vetoed={vetoed}/>

            <PreflightChecklist runtimeProps={runtimeProps}/>
            </Box>
        </Container>
    );
};

export default UserAccountInfo;
