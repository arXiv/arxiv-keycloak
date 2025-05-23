import {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Container from "@mui/material/Container";
import Tooltip from "@mui/material/Tooltip";
import PasswordRequirements from "../bits/PasswordRequirements.tsx";

import {RuntimeContext} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import {paths} from "../types/aaa-api.ts";
import {passwordValidator} from "../bits/validators.ts";
import PasswordWrapper from "../bits/PasswordWrapper.tsx";
import {useNavigate} from "react-router-dom";
import {fetchPlus} from "../fetchPlus.ts";
import CardWithTitle from "../bits/CardWithTitle.tsx";

// type AccountProfileRequest = paths["/account/profile/{user_id}"]['get']['responses']['200']['content']['application/json'];
type ChangePasswordRequest = paths["/account/password/"]['put']['requestBody']['content']['application/json'];

const ChangePassword = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const {showNotification, showMessageDialog} = useNotification();
    const [inProgress, setInProgress] = useState(false);
    const navigate = useNavigate();

    const [formData, setFormData] = useState<ChangePasswordRequest>({
        user_id: "",
        old_password: "",
        new_password: "",
    });

    const [password, setPassword] = useState<string>("");

    const [errors, setErrors] = useState<{
        old_password?: string,
        new_password?: string,
        secondPassword?: string,
    }>({old_password: "Not provided", new_password: "Not provided", secondPassword: "Not provided",});

    useEffect(() => {
        async function doSetCurrentUserID() {
            if (!user)
                return;
            setFormData({...formData, user_id: user.id});
        }

        doSetCurrentUserID();
    }, [user])


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("change password");
        setInProgress(true);
        event.preventDefault();

        try {
            const response = await fetchPlus(runtimeProps.AAA_URL + "/account/password/", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                if (response.status === 401) {
                    showMessageDialog("Please log-out and re-login before changing the password. Your log-in session has expired.", "Pleas log-in again");
                } else {
                    const errorReply = await response.json();
                    console.error(response.statusText);
                    showNotification(errorReply.detail, "warning");
                    return;
                }
            }

            showNotification("Password updated successfully", "success");
            navigate(runtimeProps.URLS.userAccountInfo);
        } catch (error) {
            console.error("Error:", error);
            showNotification(JSON.stringify(error), "warning");
        } finally {
            setInProgress(false);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
        if (name === "secondPassword") {
            setPassword(value);
        } else {
            setFormData({...formData, [name]: value});
        }
    };

    useEffect(() => {
        const updated = {
            old_password: formData.old_password ? "" : "Not provided",
            new_password: passwordValidator(formData.new_password) ? "" : "Invalid password",
            secondPassword: formData.new_password === password ? "" : "Passwords do not match",
        };
        setErrors(updated);
    }, [formData, password]);

    const invalidFormData = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );


    return (
        <Container maxWidth="sm" sx={{my: 4}}>
            <Typography variant={"h1"}>Change Password</Typography>

            <CardWithTitle title="">
                <Box component="form" sx={{display: "flex", flexDirection: "column", gap: 2}} onSubmit={handleSubmit}>
                    <PasswordRequirements/>
                    <input name="user_id" id="user_id" type="text" disabled={true} value={formData.user_id}
                           hidden={true}/>
                    <PasswordWrapper>
                        <TextField name="old_password" id="old_password" label="Old Password" type="password"
                                   fullWidth onChange={handleChange} value={formData.old_password}
                                   error={Boolean(errors.old_password)} helperText={errors.old_password}/>
                    </PasswordWrapper>
                    <PasswordWrapper>
                        <Tooltip title={<PasswordRequirements/>}>
                            <TextField name="new_password" id="new_password" label="New Password" type="password"
                                       fullWidth onChange={handleChange} value={formData.new_password}
                                       error={Boolean(errors.new_password)} helperText={errors.new_password}/>
                        </Tooltip>
                    </PasswordWrapper>
                    <PasswordWrapper>
                        <TextField name="secondPassword" label="Retype Password" type="password" fullWidth
                                   onChange={handleChange}
                                   error={Boolean(errors.secondPassword)} helperText={errors.secondPassword}
                        />
                    </PasswordWrapper>

                    <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Button variant="outlined" onClick={() => navigate("/user-account/reset-password")}>
                            Forgot Password?
                        </Button>
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
        </Container>
    );
};

export default ChangePassword;
