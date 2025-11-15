import {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Container from "@mui/material/Container";

import {RuntimeContext} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import {paths} from "../types/aaa-api.ts";
import {printUserName} from "../bits/printer.ts";
import {useNavigate} from "react-router-dom";
import CardWithTitle from "../bits/CardWithTitle.tsx";

const ACCOUNT_PROFILE_URL = "/account/{user_id}/profile";
type AccountProfileRequest = paths[typeof ACCOUNT_PROFILE_URL]['get']['responses']['200']['content']['application/json'];

const ACCOUNT_NAME_URL = "/account/{user_id}/name";
type ChangeNameRequest = paths[typeof ACCOUNT_NAME_URL]['put']['requestBody']['content']['application/json'];


const ChangeUsername = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const currentUsername = user?.username || "";
    const [inProgress, setInProgress] = useState(false);
    const {showNotification, showMessageDialog} = useNotification();
    const fullName = printUserName(user);
    const navigate = useNavigate();


    const [formData, setFormData] = useState<ChangeNameRequest>({
        username: "",
    });

    const [errors, setErrors] = useState<{
        username?: string,
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
                        username: profile.username,
                    }
                ));
            } catch (error: any) {
                console.error("Error:", error);
                showNotification(`Connection to arXiv failed - ${error.message}.`, "error")
            }
        }

        doFetchCurrentUser();
    }, [user, runtimeProps.aaaFetcher])

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        const putName = runtimeProps.aaaFetcher.path(ACCOUNT_NAME_URL).method('put').create();
        if (!user?.id)
            return;
        console.log("change username");
        event.preventDefault();
        setInProgress(true);

        try {
            await putName({user_id: user.id,  ...formData});
            showMessageDialog("Your username has been updated successfully.", "Username Changed",
                () => navigate(runtimeProps.URLS.userAccountInfo), "OK");
            showNotification("Username changed successfully", "success");
        } catch (error: any) {
            console.error("Error:", JSON.stringify(error));
            if (error?.status === 409) {
                setErrors({
                    ...errors,
                    username: `This username ${formData.username} is already taken. Please choose a different one.`
                });
            }
            else if (error?.status === 400) {
                setErrors({...errors, username: error.data?.detail || "Invalid username"});
            } else {
                showNotification(JSON.stringify(error), "error");
            }
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

        if (name === "username") {
            // Basic username validation - adjust rules as needed
            const usernameRegex = /^(?:[a-zA-Z0-9._-]{2,20}|[a-zA-Z0-9._-]{2,17}#[0-9]{1,2})$/;
            const tip = usernameRegex.test(value) ? "" : "Username must be 2-20 characters (letters, numbers, ., _, -, #nn)";
            setErrors({...errors, username: tip});
        }
    };

    const invalidFormData = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );

    const title = `Change Username for ${fullName}`
    return (
        <Container maxWidth="sm" sx={{my: "4em"}}>
            <Box display={"flex"} flexDirection={"column"} sx={{gap: "2em"}}>
                <Typography variant={"h1"}>
                    Change Username
                </Typography>

                <CardWithTitle title={title}>
                    <Box component="form" sx={{display: "flex", flexDirection: "column", gap: 2}}
                         onSubmit={handleSubmit}>
                        <Typography>
                            Your current username is {currentUsername}. Enter your new username into the
                            following form.
                        </Typography>

                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Current Username"}</Typography>
                            <Typography fontWeight={"bold"} sx={{ml: 2}}>{currentUsername}</Typography>
                            <input name="username" id="username" type="text" disabled={true} value={currentUsername}
                                   hidden={true}/>
                        </Box>
                        <TextField
                            name="username" id="username" label="New Username" type="text"
                            fullWidth onChange={handleChange} value={formData.username}
                            error={Boolean(errors.username)}
                            helperText={errors.username}
                        />

                        <TextField
                            name="comment" id="comment" label="Comment (optional)" type="text"
                            fullWidth onChange={handleChange} value={formData.comment}
                            multiline={true} rows={2}
                            helperText={false}
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
                            }} disabled={invalidFormData || inProgress || formData.username === currentUsername}>
                                Submit
                            </Button>
                        </Box>
                    </Box>
                </CardWithTitle>
            </Box>
        </Container>
    );
};

export default ChangeUsername
