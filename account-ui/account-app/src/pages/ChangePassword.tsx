import {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";
import Tooltip from "@mui/material/Tooltip";
import PasswordRequirements from "../bits/PasswordRequirements.tsx";

import {RuntimeContext} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import {paths} from "../types/aaa-api.ts";
import {passwordValidator} from "../bits/validators.ts";
import PasswordWrapper from "../bits/PasswordWrapper.tsx";
import {useNavigate} from "react-router-dom";

// type AccountProfileRequest = paths["/account/profile/{user_id}"]['get']['responses']['200']['content']['application/json'];
type ChangePasswordRequest = paths["/account/password/"]['put']['requestBody']['content']['application/json'];

const ChangePassword = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const {showNotification} = useNotification();
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
    }>({old_password: "Not provided", new_password: "Not provided", secondPassword: "Not provided", });

    useEffect(() => {
        async function doSetCurrentUserID() {
            if (!user)
                return;
            setFormData({...formData, user_id: user.id });
        }
        doSetCurrentUserID();
    }, [user])


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("change password");
        setInProgress(true);
        event.preventDefault();

        try {
            const response = await fetch(runtimeProps.AAA_URL + "/account/password/", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const errorReply =await response.json();
                console.error(response.statusText);
                showNotification(errorReply.detail, "warning");
                return;
            }

            showNotification("Password updated successfully", "success");
        } catch (error) {
            console.error("Error:", error);
            showNotification(JSON.stringify(error), "warning");
        }
        finally {
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
        const updated ={
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
        <Container maxWidth="sm" sx={{ mt: 2 }}>
            <Typography variant={"h5"}>Login to arXiv.org </Typography>

            {/* Login Form */}
            <Card elevation={0}
                  sx={{
                      p: 3,
                      position: 'relative',
                      paddingTop: '48px', // Add padding to push content down
                      marginTop: '24px', // Add margin to shift the entire card (including shadow)

                      '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: '16px', // Push the border down by 24px
                          left: 0,
                          right: 0,
                          height: '90%',
                          backgroundColor: 'transparent',
                          borderTop: '2px solid #ddd', // Add the border
                          borderLeft: '2px solid #ddd', // Add the border
                          borderRight: '2px solid #ddd', // Add the border
                          borderBottom: '2px solid #ddd', // Add the border
                      },
                  }}>

                <Box
                    sx={{
                        display: 'flex',
                        justifyContent: 'left',
                        alignItems: 'left',
                        width: '100%',
                        position: 'relative',
                        marginTop: '-44px', // Adjust this to move the title up
                        marginBottom: '16px',
                    }}
                >
                    <Typography
                        variant="h5"
                        fontWeight="normal"
                        sx={{
                            backgroundColor: 'white',
                            px: 2,
                            zIndex: 1, // Ensure the text is above the border
                        }}
                    >
                        Change Password
                    </Typography>
                </Box>

                <CardContent>
                    <Box component="form" sx={{ display: "flex", flexDirection: "column", gap: 2 }} onSubmit={handleSubmit}>
                        <PasswordRequirements />
                        <input name="user_id" id="user_id" type="text" disabled={true} value={formData.user_id} hidden={true}/>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Old Password"}</Typography>
                            <PasswordWrapper passwordInputId="old_password">
                                <TextField name="old_password" id="old_password" label="Old Password" type="password"
                                           variant="outlined" fullWidth onChange={handleChange} value={formData.old_password}
                                           error={Boolean(errors.old_password)} helperText={errors.old_password} />
                            </PasswordWrapper>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"New Password"}</Typography>
                                <PasswordWrapper passwordInputId="new_password">
                                    <Tooltip title={<PasswordRequirements />}>
                                    <TextField name="new_password" id="new_password" label="New Password" type="password"
                                               variant="outlined" fullWidth onChange={handleChange} value={formData.new_password}
                                               error={Boolean(errors.new_password)} helperText={errors.new_password} />
                                    </Tooltip>
                                </PasswordWrapper>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Retype Password"}</Typography>
                            <Tooltip title={<PasswordRequirements />}>
                                <TextField name="secondPassword" label="Retype Password" type="password" variant="outlined" fullWidth onChange={handleChange}
                                           error={Boolean(errors.secondPassword)} helperText={errors.secondPassword}
                                />
                            </Tooltip>
                        </Box>

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Button type="submit" variant="contained" sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": { backgroundColor: "#1420c0"
                                } }} disabled={invalidFormData || inProgress}>
                                Submit
                            </Button>
                            <Box flex={1} />
                            <Button variant="outlined" onClick={() => navigate("/user-account/reset-password")}>
                                Forgot Password?
                            </Button>
                        </Box>
                    </Box>
                </CardContent>
            </Card>
        </Container>
    );
};

export default ChangePassword;
