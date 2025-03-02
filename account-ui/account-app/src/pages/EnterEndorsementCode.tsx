import React, {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";

import {RuntimeContext, User} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import { paths as adminApi } from "../types/admin-api";
import {endorsementCodeValidator} from "../bits/validators";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";

type EndorsementCodeRequest = adminApi["/v1/endorsements/endorse"]['post']['requestBody']['content']['application/json'];
type EndorsementRequestType = adminApi["/v1/endorsement_requests/code"]['get']['responses']['200']['content']['application/json'];
type UserType = adminApi["/v1/users/{user_id}"]['get']['responses']['200']['content']['application/json'];

const EnterEndorsementCode = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const {showNotification} = useNotification();
    const [inProgress, setInProgress] = useState(false);
    const [endorsementRequest, setEndorsementRequest] = useState<EndorsementRequestType|null>(null);
    const [endorsee, setEndorsee] = useState<UserType|null>(null);

    const [formData, setFormData] = useState<EndorsementCodeRequest>({
        endorser_id: "",
        endorsement_code: "",
        comment: "",
        knows_personally: false,
        seen_paper: false
    });

    const [errors, setErrors] = useState<{
        endorser_id?: string,
        endorsement_code?: string,
        comment?: string,
        knows_personally?: string,
        seen_paper?: string,
        endorsee?: string,
    }>({endorser_id: "No current user", endorsement_code: "Empty"});

    useEffect(() => {
        async function doSetCurrentUserID() {
            if (!user)
                return;
            setFormData({...formData, endorser_id: user.email || "" });
            setErrors({...errors, endorser_id: user.email ? "" : "No current user. Please login."});
        }
        doSetCurrentUserID();
    }, [user])


    useEffect(() => {
        if (formData.endorsement_code) {
            async function findEndorsementRequest() {
                const query = new URLSearchParams();
                query.set("secret", formData.endorsement_code);
                try {
                    const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/endorsement_requests/code?${query.toString()}`);
                    if (response.ok) {
                        setErrors({...errors, endorsement_code: ""});
                        const body = await response.json();
                        setEndorsee(null);
                        setEndorsementRequest(body);
                    }
                    else {
                        setEndorsementRequest(null);
                        setEndorsee(null);
                        if (response.status === 404) {
                            setErrors({...errors, endorsement_code: "Not Found"});
                        }
                        const body = await response.json();
                        showNotification(body.detail, "error");
                    }
                }
                catch (error) {
                    setEndorsementRequest(null);
                    setEndorsee(null);
                    showNotification(JSON.stringify(error), "error");
                }
            }

            if (endorsementCodeValidator(formData.endorsement_code)) {
                findEndorsementRequest()
            }
            else {
                setEndorsementRequest(null);
                setEndorsee(null);
            }
        }
    }, [formData.endorsement_code]);


    useEffect(() => {
        if (endorsementRequest) {
            async function findEndorsee() {
                try {
                    const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/users/${endorsementRequest?.endorsee_id}`);
                    if (response.ok) {
                        const body: UserType = await response.json();
                        setErrors({...errors, endorsee: ""});
                        setEndorsee(body);
                    }
                    else {
                        if (response.status === 404) {
                            setErrors({...errors, endorsee: "Cannot find endorsee"});
                        }
                        const body = await response.json();
                        showNotification(body.detail, "error");
                        setEndorsee(null);
                    }
                }
                catch (error) {
                    showNotification(String(error) || "Cannot find endorsee", "error");
                    setEndorsee(null);
                }
            }

            findEndorsee();
        }
    }, [endorsementRequest]);


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        setInProgress(true);
        event.preventDefault();

        try {
            const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/endorsement/endorse/", {
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

            showNotification("Endorsement complete", "success");
        } catch (error) {
            console.error("Error:", error);
            showNotification(JSON.stringify(error), "warning");
        }
        finally {
            setInProgress(false);
        }
    };

    const handleChange = (elem: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value, checked, type} = elem.target;

        if (type === "checkbox") {
            setFormData({
                ...formData,
                [name]: !Boolean(checked),
            })
        } else {
            setFormData({
                ...formData,
                [name]: value,
            });
        }

        if (name === "endorsement_code") {
            const tip = (value) ? endorsementCodeValidator(value) ? "" : "Invalid" : "Empty";
            setErrors({...errors, endorsement_code: tip});
        }
    };

    const invalidFormData = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );

    function printUser(user: UserType | User | null) : string {
        if (!user)
            return "";
        return `${user?.first_name} ${user?.last_name} <${user?.email}> - ${user?.affiliation || "No affiliation"}`;
    }

    function printCategory(endoresementRequest: EndorsementRequestType | null) : string {
        if (!endoresementRequest)
            return "";
        return `${endoresementRequest?.archive}${ endoresementRequest?.subject_class ? "." + endoresementRequest.subject_class : ""}`;
    }

    return (
        <Container maxWidth="md" sx={{ mt: 2 }}>
            <Typography variant={"h5"}>Login to arXiv.org </Typography>

            {/* Endorse Form */}
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
                        Enter endorsement code
                    </Typography>
                </Box>

                <CardContent>
                    <Box component="form" sx={{ display: "flex", flexDirection: "column", gap: 2 }} onSubmit={handleSubmit}>
                        <Typography variant="body1" >
                            When an arXiv user requests endorsement to submit to an archive or subject class, they receive an endorsement code. To endorse a user you must get the endorsement code for that user and enter the endorsement code into the form on this page. An endorsement code is a six character alphanumeric string (ex. H6ZX2L.)
                        </Typography>
                        <input name="user_id" id="user_id" type="text" disabled={true} value={formData.endorser_id} hidden={true}/>
                        <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center" }}>
                            <Box>
                                <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Endorsement code"}</Typography>
                                <TextField tabIndex={1}
                                           sx={{width: "10em"}}
                                    name="endorsement_code" id="endorsement_code" label="Endorsement code"
                                           variant="outlined" onChange={handleChange} value={formData.endorsement_code}
                                           error={Boolean(errors.endorsement_code)} helperText={errors.endorsement_code} />
                            </Box>
                        </Box>

                        <Typography sx={{mb: 1}} >
                            <Typography component={"span"} fontWeight={"bold"}> {"Endorser: "}</Typography>
                            <Typography component={"span"} sx={{textDecoration: "underline"}}>{printUser(user)}</Typography>
                        </Typography>

                        <Typography sx={{mb: 1}} >
                            <Typography component={"span"} fontWeight={"bold"}>{"Endorsee: "}</Typography>
                            <Typography component={"span"} sx={{textDecoration: "underline"}}> {printUser(endorsee)} </Typography>
                        </Typography>

                        <Typography sx={{mb: 1}} >
                            <Typography component={"span"} fontWeight={"bold"} >{"Category: "}</Typography>
                            <Typography component={"span"} sx={{textDecoration: "underline"}}>{printCategory(endorsementRequest)}</Typography>
                        </Typography>

                        <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center" }}>
                        <FormControlLabel tabIndex={2} control={<Checkbox name="seen_paper" id="seen_paper" key={"seen_paper"} onChange={handleChange} />} label={"Seen paper"} />
                        <FormControlLabel tabIndex={3} control={<Checkbox name="knows_personally" id="knows_personally" key={"knows_personally"} onChange={handleChange} />} label={"Knows personally"} />
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Comment"}</Typography>
                            <TextField name="comment" id="comment" label="Comment" multiline
                                       variant="outlined" fullWidth onChange={handleChange}
                                       error={Boolean(errors.comment)} helperText={errors.comment}
                                       minRows={4} tabIndex={4}
                            />
                        </Box>

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Button type="submit" variant="contained" tabIndex={5} sx={{
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

export default EnterEndorsementCode;