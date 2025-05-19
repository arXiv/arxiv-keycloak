import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
// import IconButton from "@mui/material/IconButton";
import {useNotification} from "../NotificationContext";
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
import {fetchPlus} from "../fetchPlus.ts";
import {useNavigate} from "react-router-dom";
import CardWithTitle from "../bits/CardWithTitle.tsx";

type AccountProfileRequest = paths["/account/profile/{user_id}"]['get']['responses']['200']['content']['application/json'];
type UpdateProfileRequest = paths["/account/profile/"]['put']['requestBody']['content']['application/json'];
type UpdateProfileResponse = paths["/account/profile/"]['put']['responses']['200']['content']['application/json'];
// type RegistrationSuccessReply = paths["/account/register/"]['post']['responses']['200']['content']['application/json'];
type RegistrationErrorReply = paths["/account/register/"]['post']['responses']['400']['content']['application/json'];


/*
User registration and profile update shares a lot of similarity. NEEDS REFACTOR.
 */

const UpdateProfile = () => {
    const {showNotification, showMessageDialog} = useNotification();
    const runtimeProps = useContext(RuntimeContext);
    const [user, setUser] = useState<typeof runtimeProps.currentUser>(runtimeProps.currentUser);
    const navigate = useNavigate();

    // State to store input values
    const [formData, setFormData] = useState<UpdateProfileRequest>({
        id: user?.id || "",
        username: user?.username || "",
        email: user?.email || "",
        first_name: user?.first_name || "",
        last_name: user?.last_name || "",
        suffix_name: user?.suffix_name || "",
        affiliation: user?.affiliation || "",
        country: user?.country || "",
        career_status: user?.career_status || "Unknown",
        groups: user?.groups || [],
        url: user?.url || "",
        default_category: {
            archive: user?.default_category?.archive || "",
            subject_class: user?.default_category?.subject_class || ""
        },
        oidc_id: user?.oidc_id || "",
        email_verified: user?.email_verified || null,
        joined_date: user?.joined_date || null,
        scopes: user?.scopes || null,
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
                const response = await fetchPlus(runtimeProps.AAA_URL + `/account/profile/${user.id}`);
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
            } catch (e) {

            }
        }

        doFetchCurrentUser();
    }, [])

    const setSelectedGroups = (groups: CategoryGroupType[]) => {
        setFormData({...formData, groups: groups});
        if (groups.length > 0) {
            setErrors({...errors, groups: ""});
        } else {
            setErrors({...errors, groups: "Please select at least one group"});
        }
    }

    const validators: Record<string, (value: string) => void> = {
        "email": (value: string) => {
            if (!emailValidator(value)) {
                setErrors((prev) => ({...prev, email: "Invalid email format"}));
            } else {
                setErrors((prev) => ({...prev, email: ""}));
            }
        },
        "last_name": (value: string) => {
            if (value) {
                setErrors((prev) => ({...prev, last_name: ""}));
            } else {
                setErrors((prev) => ({...prev, last_name: "Last name is required"}));
            }
        }
    }

    // Handle text field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
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

    const setCarrierStatus = (value: CareerStatusType | null) => {
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
            setFormData({
                ...formData,
                default_category: {archive: cat.archive, subject_class: cat.subject_class || ""}
            });
        }
    }

    // Handle form submission
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("update " + JSON.stringify(formData));
        event.preventDefault();

        try {
            const response = await fetchPlus(runtimeProps.AAA_URL + "/account/profile/", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                const data: UpdateProfileResponse = await response.json();
                console.log("Response:", data);
                showNotification("Updated successfully", "success");
                setUser(data);
                runtimeProps.setCurrentUser(data);
            } else if (response.status === 400) {
                const message: RegistrationErrorReply = await response.json();
                showMessageDialog(message.message, "Profile update Unsuccessful");
            } else if (response.status === 401) {
                showMessageDialog("You are not logged in, or the session has expired.", "Please log-in");
            } else if (response.status === 422) {
                const data = await response.json();
                showMessageDialog(data.detail, "Failed to update your profile");
            } else {
                const message = await response.text();
                showMessageDialog(message, "Failed to update your profile");
            }

            runtimeProps.updateCurrentUser();
        } catch (error) {
            console.error("Error:", error);
            showMessageDialog(JSON.stringify(error), "Profile update was unsuccessful");
            runtimeProps.updateCurrentUser();
        }
    };

    const invalidFormData = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );

    return (
        <Container maxWidth="md" sx={{my: "4em"}}>
            {/* Registration Form */}
            <Typography variant="h1" sx={{mb: "2em"}}>
                Edit Your User Information
            </Typography>
            <CardWithTitle title="Update">

                <Box
                    component="form"
                    onSubmit={handleSubmit}
                    sx={{display: "flex", flexDirection: "column", gap: 1, p: 1}}
                >
                    <Typography variant={"body2"} fontWeight={"bold"}>
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
                    <Box sx={{display: "flex", gap: 2}}>
                        <Typography variant={"body2"}>
                            Please supply your correct name and affiliation.
                            It is a violation of our policies to misrepresent your identity or institutional
                            affiliation. Claimed affiliation should be current in the conventional sense: e.g., physical
                            presence, funding, e-mail address, mention on institutional web pages, etc.
                            Misrepresentation of identity or affiliation, for any reason, is possible grounds for
                            immediate and permanent suspension.
                            <Typography variant={"inherit"} sx={{fontWeight: "bold"}}>
                                Names and Organization fields accept pidgin TeX (\'o) for foreign characters.
                            </Typography>
                        </Typography>
                    </Box>
                    <Box>
                        <Box sx={{display: "flex", gap: 2}}>
                            <TextField
                                label="First name *"
                                error={Boolean(errors.first_name)}
                                helperText={errors.first_name}
                                name="first_name"
                                value={formData.first_name}
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 3}} // Ensures both fields take equal width
                            />
                            <TextField
                                label="Last name *"
                                error={Boolean(errors.last_name)}
                                helperText={errors.last_name}
                                name="last_name"
                                value={formData.last_name}
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 3}} // Ensures both fields take equal width
                            />
                            <TextField
                                label="Sur name"
                                error={Boolean(errors.suffix_name)}
                                helperText={errors.suffix_name}
                                name="suffix_name"
                                value={formData.suffix_name}
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 1}} // Ensures both fields take equal width
                            />
                        </Box>
                    </Box>

                    <Box>
                        <Box sx={{display: "flex", gap: 2}}>
                            <TextField
                                label="Organization *"
                                error={Boolean(errors.affiliation)}
                                helperText={errors.affiliation}
                                name="affiliation"
                                value={formData.affiliation}
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 2}} // Ensures both fields take equal width
                            />
                            <CountrySelector onSelect={setCountry} selectedCountry={formData.country || ""}/>
                            <CareerStatusSelect onSelect={setCarrierStatus} careereStatus={formData.career_status}/>
                        </Box>
                    </Box>
                    <CategoryGroupSelection selectedGroups={formData.groups as unknown as CategoryGroupType[]}
                                            setSelectedGroups={setSelectedGroups}/>
                    <Box>
                        <CategoryChooser onSelect={setDefaultCategory} selectedCategory={formData.default_category}/>
                    </Box>
                    <Box>
                        <TextField
                            label="Homepage URL"
                            name="url"
                            value={formData.url}
                            fullWidth
                            onChange={handleChange}
                            sx={{flex: 1}}
                        />
                    </Box>
                    <Box display="flex" justifyContent="space-between" alignItems="center" sx={{p: 1}}>
                        <Box sx={{flex: 1}}/>
                        <Button variant="outlined" onClick={() => navigate(runtimeProps.URLS.userAccountInfo)}>
                            Cancel
                        </Button>
                        <Box sx={{width: "16px"}}/>
                        <Button type="submit" variant="contained" disabled={invalidFormData} sx={{
                            backgroundColor: "#1976d2",
                            "&:hover": {
                                backgroundColor: "#1420c0"
                            }
                        }}>
                            Submit
                        </Button>
                    </Box>
                </Box>
            </CardWithTitle>
        </Container>
    );
};

export default UpdateProfile;
