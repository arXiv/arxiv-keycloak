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
import {RuntimeContext} from "../RuntimeContext";
import {paths} from "../types/aaa-api.ts";
import {emailValidator} from "../bits/validators.ts";
import {fetchPlus} from "../fetchPlus.ts";
import {useNavigate} from "react-router-dom";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import Link from "@mui/material/Link";
import Divider from "@mui/material/Divider";
import LinkIcon from "@mui/icons-material/Launch";

type AccountProfileRequest = paths["/account/profile/{user_id}"]['get']['responses']['200']['content']['application/json'];
type UpdateProfileRequest = paths["/account/profile/"]['put']['requestBody']['content']['application/json'];
type UpdateProfileResponse = paths["/account/profile/"]['put']['responses']['200']['content']['application/json'];
// type RegistrationSuccessReply = paths["/account/register/"]['post']['responses']['200']['content']['application/json'];
type RegistrationErrorReply = paths["/account/register/"]['post']['responses']['400']['content']['application/json'];

const LineDivider = () => <Divider sx={{borderColor: '#666', my: 2, borderBottomWidth: '2px'}}/>;
const FlexOne = () => <Box sx={{flex: 1}}/>


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

    const setCareerStatus = (value: CareerStatusType | null) => {
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
                Your User Information
            </Typography>
            <CardWithTitle title="Update user information">

                <Box
                    component="form"
                    onSubmit={handleSubmit}
                    sx={{display: "flex", flexDirection: "column", gap: 1, p: 1}}
                >

                    <Box sx={{p: 1, gap: 1}}>
                        <Typography variant="body1" fontWeight="bold" color="black" align="left" sx={{mx: 3}}>
                            It is a violation of our policies to misrepresent your identity or
                            institutional affiliation. Claimed affiliation should be current in the
                            conventional sense: e.g., physical presence, funding, e-mail address,
                            mention on institutional web pages, etc. Misrepresentation of identity or
                            affiliation, for any reason, is possible grounds for immediate and
                            permanent suspension.
                        </Typography>
                        <LineDivider/>
                        <Box sx={{display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap'}}>
                            <Typography sx={{mt: 0}} variant={"body2"}>Names accept pidgin TeX (\'o) for foreign
                                characters</Typography>
                            {
                                /*
                            <IconButton onClick={() => setExpanded((prev) => !prev)} size="small">
                                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                            <Collapse in={expanded}>
                                <Box sx={{ mt: 1 }}>
                                    <AccentedCharactersGuide />
                                </Box>
                            </Collapse>
                                */
                            }
                            <Box sx={{display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap'}}>
                                <Link
                                    sx={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: 0.5,
                                        padding: '4px 8px',
                                        whiteSpace: 'nowrap' // Prevent line break if you want it on one line
                                    }}
                                    href={runtimeProps.URLS.accentedCharactersGuide}
                                    target='_blank'
                                >
                                    <LinkIcon sx={{fontSize: 18}}/>
                                    Open Accented Characters Guide
                                </Link>
                            </Box>
                        </Box>

                        <Box sx={{display: "flex", gap: 1, pt: 2}}>
                            <TextField
                                label="First name (required)"
                                aria-label="First name or given name, required"
                                size="small"
                                error={Boolean(errors.first_name)}
                                helperText={errors.first_name}
                                name="first_name"
                                value={formData.first_name}
                                fullWidth
                                onChange={handleChange}
                            />
                            <FlexOne/>
                        </Box>

                        <Box sx={{display: "flex", gap: 1, pt: 2}}>
                            <TextField
                                label="Sur name / Last name / Family name (required)"
                                aria-label="Sur name, Last name, Family name, required"
                                size="small"
                                error={Boolean(errors.last_name)}
                                helperText={errors.last_name}
                                name="last_name"
                                value={formData.last_name}
                                fullWidth
                                onChange={handleChange}
                            />
                            <FlexOne/>
                        </Box>
                        <Box sx={{display: "flex", gap: 1, pt: 2}}>
                            <Box sx={{flex: 1}}>
                                <Typography component="label" fontWeight="bold" htmlFor="suffix_name">
                                    Suffix:
                                </Typography>
                                <Typography variant="body2" color="text.Secondary" sx={{ml: 1, mb: 0.5}}>
                                    Examples include Jr. Sr, II, etc. Do not input honorifics like Esquire or Ph.D.
                                </Typography>
                                <TextField
                                    id="suffix_name"
                                    aria-label="Suffix,examples include Jr. Sr, II, etc. Do not input honorifics like Esequire or Ph.D."
                                    size="small"
                                    error={Boolean(errors.suffix_name)}
                                    helperText={errors.suffix_name}
                                    name="suffix_name"
                                    value={formData.suffix_name}
                                    fullWidth
                                    sx={{width: "50%"}}
                                    onChange={handleChange}
                                />
                            </Box>
                        </Box>
                        <LineDivider/>
                        <Box sx={{display: "flex", gap: 1}}>
                            <Box sx={{flex: 1}}>
                                <CountrySelector onSelect={setCountry} selectedCountry={formData.country || ""}/>
                            </Box>
                            <Box sx={{flex: 1}}>
                                <CareerStatusSelect onSelect={setCareerStatus} careereStatus={formData.career_status}/>
                            </Box>
                        </Box>
                        <Box sx={{display: "flex", pt: 2}}>
                            <TextField
                                label="Organization name (required)"
                                aria-label="Your organization name, required"
                                size="small"
                                error={Boolean(errors.affiliation)}
                                helperText={errors.affiliation}
                                name="affiliation"
                                value={formData.affiliation}
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 1}}
                            />
                        </Box>

                        <Box sx={{display: "flex", pt: 2}}>
                            <TextField
                                label="Home page URL"
                                aria-label="Home page URL, optional"
                                size="small"
                                name="url"
                                value={formData.url}
                                fullWidth
                                onChange={handleChange}
                            />
                        </Box>
                    </Box>

                    <LineDivider/>

                    <Box sx={{p: 1, m: 1}}>
                        <CategoryGroupSelection selectedGroups={formData.groups as unknown as CategoryGroupType[]}
                                                setSelectedGroups={setSelectedGroups}
                        />
                        <Box sx={{pb: 1, mt: 2}}>
                            <CategoryChooser onSelect={setDefaultCategory}
                                             selectedCategory={formData.default_category}/>
                        </Box>
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
