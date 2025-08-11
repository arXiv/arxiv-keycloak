import {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Container from "@mui/material/Container";

import {RuntimeContext} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import {paths} from "../types/aaa-api.ts";
import {emailValidator} from "../bits/validators.ts";
import {printUserName} from "../bits/printer.ts";
import {useNavigate} from "react-router-dom";
import CardWithTitle from "../bits/CardWithTitle.tsx";

const ACCOUNT_PROFILE_URL = "/account/{user_id}/profile";
type AccountProfileRequest = paths[typeof ACCOUNT_PROFILE_URL]['get']['responses']['200']['content']['application/json'];

const ACCOUNT_EMAIL_URL = "/account/{user_id}/email";
type ChangeEmailRequest = paths[typeof ACCOUNT_EMAIL_URL]['put']['requestBody']['content']['application/json'];


const ChangeEmail = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const emailAddress = user?.email || "";
    const [inProgress, setInProgress] = useState(false);
    const {showNotification, showMessageDialog} = useNotification();
    const fullName = printUserName(user);
    const navigate = useNavigate();


    const [formData, setFormData] = useState<ChangeEmailRequest>({
        email: "",
        new_email: ""
    });

    const [errors, setErrors] = useState<{
        email?: string,
        new_email?: string,
    }>({});

    useEffect(() => {
        const getProfile = runtimeProps.aaaFetcher.path(ACCOUNT_PROFILE_URL).method('get').create();

        async function doFetchCurrentUser() {
            if (!user)
                return;
            setFormData({...formData});
            try {
                const response = await getProfile({user_id: user.id});
                const profile: AccountProfileRequest = response.data;
                setFormData(Object.assign({}, formData,
                    {
                        user_id: profile.id,
                        email: profile.email,
                    }
                ));
            } catch (error: any) {
                console.error("Error:", error);
                showNotification(`Connection to arXiv failed - ${error.messabe}.`, "error")
            }
        }

        doFetchCurrentUser();
    }, [user, runtimeProps.aaaFetcher])

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        const putEmail = runtimeProps.aaaFetcher.path(ACCOUNT_EMAIL_URL).method('put').create();
        if (!user?.id)
            return;
        console.log("change email");
        event.preventDefault();
        setInProgress(true);

        try {
            await putEmail({user_id: user.id,  ...formData});
            showMessageDialog("Please follow the link in the email and verify your new email address.", "Check Your Email",
                () => navigate(runtimeProps.URLS.userAccountInfo), "OK");
            showNotification("Email change successfully", "success");
        } catch (error: any) {
            console.error("Error:", error);
            showNotification(JSON.stringify(error), "error");
        } finally {
            setInProgress(false);
        }
    };

    // Handle text field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
        console.log("change: " + name + " = " + value)

        setFormData({
            ...formData,
            [name]: value,
        });

        if (name === "new_email") {
            const tip = emailValidator(value) ? "" : "Invalid email address";
            setErrors({...errors, new_email: tip});
        }
    };

    const invalidFormData = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );

    const title = `Change Email for ${fullName}`
    return (
        <Container maxWidth="sm" sx={{my: "4em"}}>
            <Box display={"flex"} flexDirection={"column"} sx={{gap: "2em"}}>
                <Typography variant={"h1"}>
                    Change Email
                </Typography>
                
                <CardWithTitle title={title}>
                    <Box component="form" sx={{display: "flex", flexDirection: "column", gap: 2}}
                         onSubmit={handleSubmit}>
                        <Typography>
                            Your current e-mail address is {emailAddress}. Enter your new e-mail address into the
                            following form; we'll send a verification code to your new e-mail address which you can use
                            to make the change.

                        </Typography>
                        <Typography>
                            Please check your e-mail and verify the new e-mail address by following the link in the
                            e-mail.
                        </Typography>

                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Old Email"}</Typography>
                            <Typography fontWeight={"bold"} sx={{ml: 2}}>{emailAddress}</Typography>
                            <input name="email" id="email" type="email" disabled={true} value={emailAddress}
                                   hidden={true}/>
                        </Box>
                        <TextField
                            name="new_email" id="new_email" label="New Email" type="email"
                            fullWidth onChange={handleChange} value={formData.new_email}
                            error={Boolean(errors.new_email)}
                            helperText={errors.new_email}
                        />

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Box flex={1}/>
                            <Button variant="outlined" onClick={() => navigate(runtimeProps.URLS.userAccountInfo)}>
                                Cancel
                            </Button>
                            <Box sx={{width: "16px"}}/>

                            <Button type="submit" variant="contained" sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": {
                                    backgroundColor: "#1420c0"
                                }
                            }} disabled={invalidFormData || inProgress}>
                                Submit
                            </Button>
                        </Box>
                    </Box>
                </CardWithTitle>
            </Box>
        </Container>
    );
};

export default ChangeEmail