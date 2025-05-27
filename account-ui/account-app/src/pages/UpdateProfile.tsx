import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
// import IconButton from "@mui/material/IconButton";
import {useNotification} from "../NotificationContext";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";

import React, {useContext, useEffect, useState} from "react";
import {RuntimeContext} from "../RuntimeContext";
import {paths} from "../types/aaa-api.ts";
import {fetchPlus} from "../fetchPlus.ts";
import {useNavigate} from "react-router-dom";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import LineDivider from "../bits/LineDevider.tsx";
import {AccountFormError} from "./demographic/AccountFormError.ts";
import UserInfoForm from "./demographic/UserInforForm.tsx";
import SubmissionCategoryForm from "./demographic/SubmissionCategoryForm.tsx";

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

    const [errors, setErrors] = useState<AccountFormError>({});

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
