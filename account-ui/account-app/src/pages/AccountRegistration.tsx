import {Box, Button, IconButton, Card, CardContent, Container, TextField, Typography, Link } from "@mui/material";
import React, {useCallback, useContext, useEffect, useState} from "react";
import CategorySelection, {CategoryGroupType} from "../bits/CategorySelection.tsx";
import CategoryChooser from "../bits/CategoryChooser.tsx";
import CountrySelector from "../bits/CountrySelector.tsx";
import CareerStatusSelect from "../bits/CareerStatus.tsx";
import {RuntimeContext} from "../RuntimeContext.tsx";
import {paths} from "../types/aaa-api.ts";
import RefreshIcon from "@mui/icons-material/Refresh";

type TokenResponse = paths["/account/register/"]['get']['responses']['200']['content']['application/json'];
type SubmitRequest = paths["/account/register/"]['post']['requestBody']['content']['application/json'];


const AccountRegistration = () => {
    const runtimeContext = useContext(RuntimeContext);
    // State to store input values
    const [formData, setFormData] = useState<SubmitRequest>({
        username: "",
        email: "",
        password: "",
        first_name: "",
        last_name: "",
        suffix_name: "",
        affiliation: "",
        country: "",
        career_status: "",
        groups: [],
        url: "",
        default_category: {archive: "", subject_class: ""},
        joined_date: 0,
        oidc_id: "",
        origin_ip: null,
        origin_host: null,
        token: "",
        captcha_value: "",
        keycloak_migration: false
    });

    const [secondPassword, setSecondPassword] = useState("");

    const [errors, setErrors] = useState<{
        username?: string,
        email?: string,
        password?: string,
        secondPassword?: string,
        first_name?: string,
        last_name?: string,
        suffix_name?: string,
        affiliation?: string,
        country?: string,
        career_status?: string,
        groups?: string[],
        default_category?: string,
        captcha_value?: string
    }>({});

    const [token, setToken] = useState<string|null>(null);
    const [captchaImage, setCaptchaImage] = useState<React.ReactNode|null>(null);

    const [selectedGroups, setSelectedGroups] = useState<CategoryGroupType[]>([]); // Default checked value
    /*
                <ToggleButton value="flag_group_cs">cs</ToggleButton>
                <ToggleButton value="flag_group_econ">econ</ToggleButton>
                <ToggleButton value="flag_group_eess">eess</ToggleButton>
                <ToggleButton value="flag_group_math">math</ToggleButton>
                <ToggleButton value="flag_group_physics">physics</ToggleButton>
                <ToggleButton value="flag_group_q_bio">q-bio</ToggleButton>
                <ToggleButton value="flag_group_q_fin">q-fin</ToggleButton>
                <ToggleButton value="flag_group_stat">stat</ToggleButton>
     */


    useEffect(() => {
        console.log(JSON.stringify(formData));
        if (token) {
            setCaptchaImage(
                <img alt={"captcha"} src={runtimeContext.AAA_URL + `/captcha/image?token=${token}`}/>
            )
        }
        else {
            fetch(runtimeContext.AAA_URL + "/account/register/")
                .then(response => response.json()
                    .then((data: TokenResponse) => setToken(data.token)));
        }
    }, [token]);

    const resetCaptcha = useCallback(() => {
        setToken(null);
    }, []);


    const validateEmail = (email: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    // Handle text field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;

        if (name === "secondPassword") {
            setSecondPassword(value);
        }
        else if (name === "token") {
            setToken(value);
        }
        else {
            setFormData({
                ...formData,
                [name]: value,
            });
        }

        if (name === "username") {
            const minUsernameLength = 3;
            if (value.length < minUsernameLength) {
                setErrors((prev) => ({ ...prev, username: `User name must be minimum of ${minUsernameLength} characters` }));
            } else {
                setErrors((prev) => ({ ...prev, username: undefined }));
            }
        }

        if (name === "password") {
            if (value.length < 10) {
                setErrors((prev) => ({ ...prev, password: "Password must be at least 10 characters" }));
            } else {
                setErrors((prev) => ({ ...prev, password: undefined }));
            }
        }

        if (name === "secondPassword") {
            if (value !== formData.password) {
                setErrors((prev) => ({ ...prev, secondPassword: "Reentered password does not match" }));
            } else {
                setErrors((prev) => ({ ...prev, secondPassword: undefined }));
            }
        }

        // Validate email
        if (name === "email") {
            if (!validateEmail(value)) {
                setErrors((prev) => ({ ...prev, email: "Invalid email format" }));
            } else {
                setErrors((prev) => ({ ...prev, email: "" }));
            }
        }
    };

    // Handle form submission
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("Submit");
        event.preventDefault();

        if (!formData.captcha_value) {
            alert("Please complete the CAPTCHA before submitting.");
            return;
        }
        try {
            const response = await fetch(runtimeContext.AAA_URL + "/account/register/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                throw new Error("Failed to register");
            }

            const data = await response.json();
            alert("Registration successful!");
            console.log("Response:", data);
        } catch (error) {
            console.error("Error:", error);
            alert("Registration failed.");
        }
    };

    const invalidFormData = formData.username.length < 2 || formData.password.length < 10 || formData.password !== secondPassword;

    return (
        <Container maxWidth="md" sx={{ mt: 2 }} >
            <Typography variant={"h5"}>Register for the first time</Typography>
            {/* Privacy Policy Notice */}
            <Card elevation={3} sx={{ p: 3, mb: 3, backgroundColor: "#eeeef8" }}>
                <Typography variant="body1" fontWeight={"bold"} color="textSecondary" align="left">
                    {"By registering with arXiv you are agreeing to the "}
                    <Link href="https://arxiv.org/help/policies/privacy_policy" target="_blank" rel="noopener" underline="hover">
                        arXiv Privacy Policy
                    </Link>
                    {"."}
                </Typography>
            </Card>

            {/* Registration Form */}
            <Card elevation={0}
                  sx={{
                      p: 1,
                      position: 'relative',
                      paddingTop: '48px', // Add padding to push content down
                      marginTop: '24px', // Add margin to shift the entire card (including shadow)

                      '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: '16px', // Push the border down by 24px
                          left: 0,
                          right: 0,
                          height: '95%',
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
                        Account registration
                    </Typography>
                </Box>

                <CardContent sx={{py: 0}} >
                    <Box
                        component="form"
                        onSubmit={handleSubmit}
                        sx={{ display: "flex", flexDirection: "column", gap: 1 }}
                    >
                        <Typography variant={"body2"} fontWeight={"bold"} >
                            Fields with * are required.
                        </Typography>

                        <Box sx={{ display: "flex", gap: 2 }}>
                        <TextField label="Username *" sx={{ flex: 1 }}
                                   error={Boolean(errors.username)}
                                   helperText={errors.username}
                                   name="username" value={formData.username} variant="outlined" fullWidth  onChange={handleChange} />
                        <TextField label="Email *" sx={{ flex: 2 }}
                                   error={Boolean(errors.email)}
                                   helperText={errors.email}
                                   name="email" value={formData.email} variant="outlined" fullWidth  onChange={handleChange} />
                        </Box>
                        <Box sx={{ display: "flex", gap: 2 }}>
                            <TextField
                                label="Password *"
                                error={Boolean(errors.password)}
                                helperText={errors.password}
                                name="password"
                                value={formData.password}
                                type="password"
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ flex: 1 }} // Ensures both fields take equal width
                            />

                            <TextField
                                label="Reenter Password *"
                                error={Boolean(errors.secondPassword)}
                                helperText={errors.secondPassword}
                                name="secondPassword"
                                value={secondPassword}
                                type="password"
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ flex: 1 }} // Ensures both fields take equal width
                            />
                        </Box>
                        <Box  sx={{ display: "flex", gap: 2 }}>
                            <Typography variant={"body2"}>
                                Please supply your correct name and affiliation.
                                It is a violation of our policies to misrepresent your identity or institutional affiliation. Claimed affiliation should be current in the conventional sense: e.g., physical presence, funding, e-mail address, mention on institutional web pages, etc. Misrepresentation of identity or affiliation, for any reason, is possible grounds for immediate and permanent suspension.
                                <Typography variant={"inherit"} sx={{fontWeight: "bold"}}>
                                    Names and Organization fields accept pidgin TeX (\'o) for foreign characters.
                                </Typography>
                            </Typography>
                        </Box>
                        <Box sx={{ display: "flex", gap: 2 }}>
                            <TextField
                                label="First name *"
                                error={Boolean(errors.first_name)}
                                helperText={errors.first_name}
                                name="first_name"
                                value={formData.first_name}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ flex: 3 }} // Ensures both fields take equal width
                            />
                            <TextField
                                label="Last name *"
                                error={Boolean(errors.last_name)}
                                helperText={errors.last_name}
                                name="last_name"
                                value={formData.last_name}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ flex: 3 }} // Ensures both fields take equal width
                            />
                            <TextField
                                label="Sur name"
                                error={Boolean(errors.suffix_name)}
                                helperText={errors.suffix_name}
                                name="suffix_name"
                                value={formData.suffix_name}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ flex: 1 }} // Ensures both fields take equal width
                            />
                        </Box>

                        <Box sx={{ display: "flex", gap: 2 }}>
                            <TextField
                                label="Organization *"
                                error={Boolean(errors.affiliation)}
                                helperText={errors.affiliation}
                                name="affiliation"
                                value={formData.affiliation}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ flex: 3 }} // Ensures both fields take equal width
                            />
                            <CountrySelector />
                            <CareerStatusSelect />
                        </Box>
                        <CategorySelection selectedGroups={selectedGroups} setSelectedGroups={setSelectedGroups} />
                        <CategoryChooser />
                        <TextField
                            label="Your Homepage URL"
                            name="url"
                            value={formData.url}
                            variant="outlined"
                            fullWidth
                            onChange={handleChange}
                            sx={{ flex: 1 }}
                        />

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            {captchaImage}
                            <IconButton onClick={resetCaptcha} > <RefreshIcon /></IconButton>

                            <TextField
                                label="Captcha Respones *"
                                name="captcha_value"
                                value={formData.captcha_value}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ width: "12em" }}
                            />
                            <Box sx={{flex: 1}} />

                            <Button type="submit" variant="contained" disabled={invalidFormData} sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": { backgroundColor: "#1420c0"
                                } }} >
                                Submit
                            </Button>
                        </Box>
                    </Box>
                </CardContent>
            </Card>

        </Container>
    );
};

export default AccountRegistration;
