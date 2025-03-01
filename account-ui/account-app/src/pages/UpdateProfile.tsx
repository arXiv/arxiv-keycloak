import Box from "@mui/material/Box";
import Button  from "@mui/material/Button";
// import IconButton from "@mui/material/IconButton";
import { useNotification } from "../NotificationContext";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import React, {useContext, useEffect, useState} from "react";
import CategoryGroupSelection, {CategoryGroupType} from "../bits/CategoryGroupSelection.tsx";
import CategoryChooser, {SelectedCategoryType} from "../bits/CategoryChooser.tsx";
import CountrySelector from "../bits/CountrySelector.tsx";
import CareerStatusSelect, {CareerStatusType} from "../bits/CareerStatus.tsx";
import {RuntimeContext} from "../RuntimeContext.tsx";
import {paths} from "../types/aaa-api.ts";
import {emailValidator} from "../bits/validators.ts";

type AccountProfileRequest = paths["/account/profile/{user_id}"]['get']['responses']['200']['content']['application/json'];
type UpdateProfileRequest = paths["/account/profile/"]['put']['requestBody']['content']['application/json'];
// type RegistrationSuccessReply = paths["/account/register/"]['post']['responses']['200']['content']['application/json'];
type RegistrationErrorReply = paths["/account/register/"]['post']['responses']['400']['content']['application/json'];


/*
User registration and profile update shares a lot of similarity. NEEDS REFACTOR.
 */

const UpdateProfile = () => {
    const {showNotification, showMessageDialog} = useNotification();
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;

    // State to store input values
    const [formData, setFormData] = useState<UpdateProfileRequest>({
        id: "",
        username: "",
        email: "",
        first_name: "",
        last_name: "",
        suffix_name: "",
        affiliation: "",
        country: "",
        career_status: "Unknown",
        groups: [],
        url: "",
        default_category: {archive: "", subject_class: ""},
        oidc_id: "",
        email_verified: null,
        joined_date: null,
        scopes: null,
    });

    const [errors, setErrors] = useState<{
        username?: string,
        email?: string,
        password?: string,
        first_name?: string,
        last_name?: string,
        suffix_name?: string,
        affiliation?: string,
        country?: string,
        career_status?: string,
        groups?: string,
        default_category?: string,
    }>({});

    useEffect(() => {
        async function doFetchCurrentUser() {
            if (!user)
                return;
            try {
                const response = await fetch(runtimeProps.AAA_URL + `/account/profile/${user.id}`);
                if (!response.ok) {
                    showNotification("Fetching user failed", "error")
                    return;
                }
                const profile: AccountProfileRequest = await response.json();
                console.log(JSON.stringify(profile));
                setFormData(Object.assign({}, formData,
                    {
                        id: profile.id,
                        username: profile.username,
                        email: profile.email,
                        first_name: profile.first_name,
                        last_name: profile.last_name,
                        suffix_name: profile.suffix_name,
                        affiliation: profile.affiliation,
                        country: profile.country,
                        career_status: profile.career_status,
                        groups: profile.groups,
                        default_category: profile.default_category,
                        url: profile.url,
                    }
                ));
            }
            catch (e) {

            }
        }
        doFetchCurrentUser();
    }, [user])

    const setSelectedGroups = (groups: CategoryGroupType[]) => {
        setFormData({...formData, groups: groups});
        if (groups.length > 0) {
            setErrors({ ...errors, groups: "" });
        }
        else {
            setErrors({ ...errors, groups: "Please select at least one group" });
        }
    }

    const validators: Record<string, (value: string) => void> = {
        "email": (value: string) => {
            if (!emailValidator(value)) {
                setErrors((prev) => ({ ...prev, email: "Invalid email format" }));
            } else {
                setErrors((prev) => ({ ...prev, email: "" }));
            }
        },
    }

    // Handle text field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        console.log("change: " + name + " = " + value)

        setFormData({
            ...formData,
            [name]: value,
        });

        const validator = validators[name];
        if (validator) {
            validator(value)
        }
    };

    const setCarrerStatus = (value: CareerStatusType | null) => {
        if (value) {
            setFormData({...formData, career_status: value})
        }
    };

    const setCountry = (value: string | null) => {
        if (value) {
            setFormData({...formData, country: value})
        }
    };

    const setDefaultCategory = (cat: SelectedCategoryType) => {
        if (cat) {
            console.log("sdc: " + JSON.stringify(cat));
            setFormData({...formData, default_category: {archive: cat.archive, subject_class: cat.subject_class || ""}});
        }
    }

    // Handle form submission
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("update");
        event.preventDefault();

        try {
            const response = await fetch(runtimeProps.AAA_URL + "/account/profile/", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });
            const data = await response.json();
            console.log("Response:", data);

            if (response.ok) {
                showNotification("Updated succesfully", "success");
            }
            else if (response.status === 400) {
                const reply: RegistrationErrorReply = data as any;
                showMessageDialog(reply.message, "Profile update Unsuccessful");
            }

        } catch (error) {
            console.error("Error:", error);
            showMessageDialog(JSON.stringify(error), "Registration Unsuccessful");
        }
    };

    const invalidFormData = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );

    return (
        <Container maxWidth="md" sx={{ mt: 3 }}>
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
                          border: '2px solid #ddd', // Add the border
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
                        Edit Your User Information
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

                        {
                            /*
                        <Box >
                            <Typography fontWeight={"bold"}>{"Email: "}</Typography>
                            <Typography sx={{paddingLeft: 3, mb: 1}}>{"You "}
                                <Typography component="span" fontWeight="bold">{"must"}</Typography>
                                {" able to receive mail at this address to register. We take "}
                                <Link href={runtimeProps.URLS.emailProtection} target="_blank" rel="noopener" underline="hover">strong measure</Link>
                                {" to protect your email address from viruses and spam. Do not register with an e-mail address that belongs to someone else: if we discover that you've done so, we will suspend your account."}
                            </Typography>
                            <TextField label="Email *" sx={{ flex: 2 }}
                                       error={Boolean(errors.email)}
                                       helperText={errors.email}
                                       name="email" value={formData.email} variant="outlined" fullWidth  onChange={handleChange} />
                        </Box>

                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"User name: "}</Typography>
                            <Box sx={{ display: "flex", gap: 2 }}>
                                <TextField label="Username *" sx={{ flex: 1 }}
                                           error={Boolean(errors.username)}
                                           helperText={errors.username}
                                           name="username" value={formData.username} variant="outlined" fullWidth  onChange={handleChange} />
                            </Box>
                        </Box>

                             */
                        }
                        <Box  sx={{ display: "flex", gap: 2 }}>
                            <Typography variant={"body2"}>
                                Please supply your correct name and affiliation.
                                It is a violation of our policies to misrepresent your identity or institutional affiliation. Claimed affiliation should be current in the conventional sense: e.g., physical presence, funding, e-mail address, mention on institutional web pages, etc. Misrepresentation of identity or affiliation, for any reason, is possible grounds for immediate and permanent suspension.
                                <Typography variant={"inherit"} sx={{fontWeight: "bold"}}>
                                    Names and Organization fields accept pidgin TeX (\'o) for foreign characters.
                                </Typography>
                            </Typography>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"First, Last and Sur name:  "}</Typography>
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
                        </Box>

                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Organization, Country and Career Status:  "}</Typography>
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
                                <CountrySelector onSelect={setCountry} selectedCountry={formData.country || ""}/>
                                <CareerStatusSelect onSelect={setCarrerStatus} careereStatus={formData.career_status}/>
                            </Box>
                        </Box>
                        <CategoryGroupSelection selectedGroups={formData.groups as unknown as CategoryGroupType[]} setSelectedGroups={setSelectedGroups} />
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Your default category:  "}</Typography>
                            <CategoryChooser onSelect={setDefaultCategory} selectedCategory={formData.default_category} />
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Home page URL:  "}</Typography>
                            <TextField
                                label="Your Homepage URL"
                                name="url"
                                value={formData.url}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{ flex: 1 }}
                            />
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center" sx={{p:1}}>
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

export default UpdateProfile;
