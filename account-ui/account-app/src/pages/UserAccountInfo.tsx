import React, {useCallback, useContext, useEffect, useState} from "react";
import Container from '@mui/material/Container'
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Box from "@mui/material/Box";

import VerifiedUser from "@mui/icons-material/VerifiedUser";

import {RuntimeContext, RuntimeProps} from "../RuntimeContext.tsx";
import YesNoDialog from "../bits/YesNoDialog.tsx";
// import SubmissionsTable from "../bits/SubmissionsTable.tsx";
import YourSubmissions from "../components/YourSubmissions.tsx";
import {useNotification} from "../NotificationContext.tsx";

import {ACCOUNT_USER_EMAIL_VERIFY_URL} from "../types/aaa-url.ts";
import UserDocumentList from "../components/UserDocumentList.tsx";
import YourAccountInfo from "../components/YourAccountInfo.tsx";
import Button from "@mui/material/Button";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import {ArticleInfo} from "./YourDocuments.tsx";



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

    console.log(JSON.stringify(user));

    useEffect(() => {
        if (runtimeProps.updateCurrentUser)
            runtimeProps.updateCurrentUser();
    }, []);


    useEffect(() => {
        if (!runtimeProps.currentUser)
            showMessageDialog("Please log in first", "No user", () => <Link href={"/login"}/>);
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

    return (
        <Container maxWidth={"lg"} sx={{my: "4em", gap: 1}}>
            <Box display={"flex"} flexDirection={"column"} sx={{gap: "0.75em"}}>
                <Typography variant={"h1"} >Account for {user?.first_name} {user?.last_name} </Typography>

                <YourSubmissions runtimeProps={runtimeProps} vetoed={vetoed}/>
                <CardWithTitle title={"Articles You Own"}>
                    <UserDocumentList />
                    <ArticleInfo />
                </CardWithTitle>
                <YourAccountInfo runtimeProps={runtimeProps} VerifyEmailButton={VerifyEmailButton}/>
            </Box>
        </Container>
    );
};

export default UserAccountInfo;
