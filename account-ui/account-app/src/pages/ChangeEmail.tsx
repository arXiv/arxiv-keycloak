import {useContext, useEffect, useState} from "react";
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
import {emailValidator} from "../bits/validators.ts";

type AccountProfileRequest = paths["/account/profile/{user_id}"]['get']['responses']['200']['content']['application/json'];
type ChangeEmailRequest = paths["/account/email/"]['put']['requestBody']['content']['application/json'];

const ChangeEmail = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const emailAddress = user?.email || "";
    const [inProgress, setInProgress] = useState(false);
    const {showNotification, showMessageDialog} = useNotification();

    const [formData, setFormData] = useState<ChangeEmailRequest>({
        user_id: "",
        email: "",
        new_email: ""
    });

    const [errors, setErrors] = useState<{
        email?: string,
        new_email?: string,
    }>({});

    useEffect(() => {
        async function doFetchCurrentUser() {
            if (!user)
                return;
            setFormData({...formData, user_id: user.id });
            try {
                const response = await fetch(runtimeProps.AAA_URL + `/account/profile/${user.id}`);
                if (!response.ok) {
                    const data = await response.json();
                    showNotification("Connection to arXiv failed. " + data.detail, "error")
                    return;
                }
                const profile: AccountProfileRequest = await response.json();
                setFormData(Object.assign({}, formData,
                    {
                        user_id: profile.id,
                        email: profile.email,
                    }
                ));
            }
            catch (err) {
                showNotification(`Connection to arXiv failed - ${err}.`, "error")
            }
        }
        doFetchCurrentUser();
    }, [user])

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("change email");
        event.preventDefault();
        setInProgress(true);

        try {
            const response = await fetch(runtimeProps.AAA_URL + "/account/email/", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });
            if (!response.ok) {
                console.error(response.statusText);
                const errorResponse = await response.json();
                showNotification(errorResponse.detail, "warning");
                return;
            }

            showMessageDialog("Please follow the link in the email and verify your new email address.", "Check Your Email");
            showNotification("Email change successfully", "success");
        } catch (error) {
            console.error("Error:", error);
            showNotification(JSON.stringify(error), "warning");
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

    return (
        <Container maxWidth="sm" sx={{ mt: 0 }}>
            <Typography variant={"h5"}>Login to arXiv.org </Typography>

            {/* Change email Form */}
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
                        {`Change Email for ${emailAddress}`}
                    </Typography>
                </Box>

                <CardContent>
                    <Box component="form" sx={{ display: "flex", flexDirection: "column", gap: 2 }} onSubmit={handleSubmit}>
                        <input name="user_id" id="user_id" type="text" disabled={true} value={formData.user_id} hidden={true}/>
                        <Typography>
                            Your current e-mail address is {emailAddress}. Enter your new e-mail address into the following form; we'll send a verification code to your new e-mail address which you can use to make the change.
                        </Typography>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Old Email"}</Typography>
                            <Typography fontWeight={"bold"} sx={{ml: 2}}>{emailAddress}</Typography>
                            <input name="email" id="email" type="email"  disabled={true} value={emailAddress} hidden={true}/>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"New Email"}</Typography>
                            <TextField
                                name="new_email" id="new_email" label="New Email" type="email" variant="outlined"
                                fullWidth onChange={handleChange} value={formData.new_email} error={Boolean(errors.new_email)}
                                helperText={errors.new_email}
                            />
                        </Box>

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Button type="submit" variant="contained" sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": { backgroundColor: "#1420c0"
                                } }} disabled={invalidFormData || inProgress}>
                                Submit
                            </Button>
                        </Box>
                    </Box>
                </CardContent>
            </Card>
        </Container>
    );
};

export default ChangeEmail