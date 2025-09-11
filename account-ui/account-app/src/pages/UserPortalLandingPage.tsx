import {useContext, useEffect} from "react";
import Container from '@mui/material/Container'
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import Box from "@mui/material/Box";

import {RuntimeContext} from "../RuntimeContext.tsx";
// import SubmissionsTable from "../bits/SubmissionsTable.tsx";
import YourSubmissions from "../components/YourSubmissions.tsx";
import {useNotification} from "../NotificationContext.tsx";

import UserDocumentList from "../components/UserDocumentList.tsx";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import {ArticleInfo} from "./YourDocuments.tsx";
import LinkIcon from "@mui/icons-material/Launch";
import IconButton from "@mui/material/IconButton";
import {useNavigate} from "react-router-dom";


const UserPortalLandingPage = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const {showMessageDialog} = useNotification();
    const navigate = useNavigate();

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
                <Typography variant={"h1"} >Account for {user?.first_name} {user?.last_name}
                    <IconButton onClick={() => navigate("/user-account/info")}  >
                        <LinkIcon />{"Account Information"}
                    </IconButton>
                </Typography>

                <YourSubmissions runtimeProps={runtimeProps} vetoed={vetoed}/>
                <CardWithTitle title={"Articles You Own"}>
                    <UserDocumentList />
                    <ArticleInfo />
                </CardWithTitle>
            </Box>
        </Container>
    );
};

export default UserPortalLandingPage;
