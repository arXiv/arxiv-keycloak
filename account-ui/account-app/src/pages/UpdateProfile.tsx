import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
// import IconButton from "@mui/material/IconButton";
import {useNotification} from "../NotificationContext";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";

import React, {useContext, useEffect, useState} from "react";
import {RuntimeContext} from "../RuntimeContext";
import {paths} from "../types/aaa-api.ts";
// import {fetchPlus} from "../fetchPlus.ts";
import {useNavigate} from "react-router-dom";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import LineDivider from "../bits/LineDevider.tsx";
import {AccountFormError} from "./demographic/AccountFormError.ts";
import UserInfoForm from "./demographic/UserInfoForm.tsx";
import SubmissionCategoryForm from "./demographic/SubmissionCategoryForm.tsx";
import {ACCOUNT_PROFILE_URL, ACCOUNT_REGISTER_URL} from "../types/aaa-url.ts";


type AccountProfileRequest = paths[typeof ACCOUNT_PROFILE_URL]['get']['responses']['200']['content']['application/json'];
type UpdateProfileRequest = paths[typeof ACCOUNT_PROFILE_URL]['put']['requestBody']['content']['application/json'];
type RegistrationErrorReply = paths[typeof ACCOUNT_REGISTER_URL]['post']['responses']['400']['content']['application/json'];

/*
User registration and profile update share a lot of similarities. NEEDS REFACTOR.
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

    const [errors, setErrors] = useState<AccountFormError>({});

    useEffect(() => {
        async function doFetchCurrentUser() {
            if (!user)
                return;

            const getProfile = runtimeProps.aaaFetcher.path(ACCOUNT_PROFILE_URL).method('get').create();

            try {
                const response = await getProfile({user_id: user.id});
                const profile: AccountProfileRequest = response.data;
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
                console.error("Error fetching user profile:", e);
                showNotification("Error fetching user profile", "error");
            }
        }

        doFetchCurrentUser();
    }, [runtimeProps.aaaFetcher])


    // Handle form submission
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("update " + JSON.stringify(formData));
        event.preventDefault();

        const putProfile = runtimeProps.aaaFetcher.path(ACCOUNT_PROFILE_URL).method('put').create();

        try {
            const response = await putProfile({user_id: user?.id || "", ...formData});
            showNotification("Updated successfully", "success");
            runtimeProps.setCurrentUser(response.data);
            setUser(response.data);
            runtimeProps.updateCurrentUser();
        } catch (error: any) {
            console.error("Error:", error);
            if (error.status === 400 && error.data) {
                const errorData: RegistrationErrorReply = error.data;
                const errorMessage = Array.isArray(errorData) ? errorData.map(e => e.message).join(", ") : (errorData as any).message || JSON.stringify(errorData);
                showMessageDialog(errorMessage, "Profile update Unsuccessful");
            } else if (error.status === 401) {
                showMessageDialog("You are not logged in, or the session has expired.", "Please log-in");
            } else if (error.status === 422 && error.data) {
                showMessageDialog(error.data.detail, "Failed to update your profile");
            } else {
                showMessageDialog(error.message || JSON.stringify(error), "Profile update was unsuccessful");
            }
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

                    <UserInfoForm formData={formData} setFormData={setFormData} errors={errors} setErrors={setErrors} />

                    <LineDivider/>

                    <SubmissionCategoryForm formData={formData} setFormData={setFormData} setErrors={setErrors} />

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
