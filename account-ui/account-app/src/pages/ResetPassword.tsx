import {useContext, useState} from "react";
import Typography from "@mui/material/Typography";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";

import {RuntimeContext} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import {paths} from "../types/aaa-api.ts";

// type AccountProfileRequest = paths["/account/profile/{user_id}"]['get']['responses']['200']['content']['application/json'];
type ResetPasswordRequest = paths["/account/password/reset/"]['post']['requestBody']['content']['application/json'];

const ResetPassword = () => {
    const runtimeProps = useContext(RuntimeContext);
    const {showNotification, showMessageDialog} = useNotification();
    const [inProgress, setInProgress] = useState(false);

    const [formData, setFormData] = useState<ResetPasswordRequest>({
        username_or_email: runtimeProps.currentUser ? runtimeProps.currentUser.email : "",
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
        setFormData({...formData, [name]: value});
    };


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("reset password");
        setInProgress(true);
        event.preventDefault();

        try {
            const response = await fetch(runtimeProps.AAA_URL + "/account/password/reset/", {
                method: "POST",
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

            showMessageDialog("Your request for password recovery has been started. Please check your email", "Password reset in progress");
        } catch (error) {
            console.error("Error:", error);
            showNotification(JSON.stringify(error), "warning");
        }
        finally {
            setInProgress(false);
        }
    };

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
                        Reset Password
                    </Typography>
                </Box>

                <CardContent>
                    <Typography variant={"body1"} sx={{mb: 1}}>{"We will send you an email for password recovery. Follow the instructions in the email to reset the password."}</Typography>

                    <Box component="form" sx={{ display: "flex", flexDirection: "column", gap: 2 }} onSubmit={handleSubmit}>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Username or email"}</Typography>
                            <TextField name="username_or_email" id="username_or_email" label="User name or email"
                                       variant="outlined" fullWidth  value={formData.username_or_email}
                                       onChange={handleChange} />
                        </Box>

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Button type="submit" variant="contained" sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": { backgroundColor: "#1420c0"
                                } }} disabled={inProgress}>
                                Submit
                            </Button>
                            <Box flex={1} />
                        </Box>
                    </Box>
                </CardContent>
            </Card>
        </Container>
    );
};

export default ResetPassword;