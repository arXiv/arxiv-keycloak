import React, {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";

import {RuntimeContext, User} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import {paths as adminApi} from "../types/admin-api";
import {endorsementCodeValidator} from "../bits/validators";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
// import{RadioButtonChecked from "@mui/icons-material";
import FormControl from "@mui/material/FormControl";
import RadioGroup from "@mui/material/RadioGroup";
import Radio from "@mui/material/Radio";
import CardHeader from "@mui/material/CardHeader";

type EndorsementCodeRequest = adminApi["/v1/endorsements/endorse"]['post']['requestBody']['content']['application/json'];
type Endorsement405Response = adminApi["/v1/endorsements/endorse"]['post']['responses']['405']['content']['application/json'];
type EndorsementRequestType = adminApi["/v1/endorsement_requests/code"]['get']['responses']['200']['content']['application/json'];
type PublicUserType = adminApi["/v1/public-users/{user_id}"]['get']['responses']['200']['content']['application/json'];
type CategoryResponse = adminApi["/v1/categories/{archive}/subject-class/{subject_class}"]['get']['responses']['200']['content']['application/json'];


const EnterEndorsementCode = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const {showNotification, showMessageDialog} = useNotification();
    const [inProgress, setInProgress] = useState(false);
    const [endorsementRequest, setEndorsementRequest] = useState<EndorsementRequestType | null>(null);
    const [endorsementCategoryName, setEndorsementCategoryName] = useState<string | null>(null);

    const [endorsee, setEndorsee] = useState<PublicUserType | null>(null);

    const [formData, setFormData] = useState<EndorsementCodeRequest>({
        endorser_id: "",
        positive: true,
        endorsement_code: "",
        comment: "",
        knows_personally: false,
        seen_paper: false
    });

    const [errors, setErrors] = useState<{
        endorser_id?: string,
        positive?: boolean,
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
            setFormData({...formData, endorser_id: user?.id || ""});
            setErrors({...errors, endorser_id: user?.id ? "" : "No current user. Please login."});
        }

        doSetCurrentUserID();
    }, [user])


    useEffect(() => {
        async function findEndorsementRequest() {
            if (formData?.endorsement_code) {
                const query = new URLSearchParams();
                query.set("secret", formData.endorsement_code);
                try {
                    const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/endorsement_requests/code?${query.toString()}`);
                    if (response.ok) {
                        setErrors({...errors, endorsement_code: ""});
                        const body = await response.json();
                        setEndorsee(null);
                        setEndorsementRequest(body);
                    } else {
                        setEndorsementRequest(null);
                        setEndorsee(null);
                        if (response.status === 404) {
                            setErrors({...errors, endorsement_code: "Not Found"});
                        } else if (response.status === 401) {
                            setErrors({...errors, endorsement_code: "Please login"});
                            showMessageDialog("Please re-login first.", "No User Information",
                                () => {
                                }, "OK",
                                () => {
                                    window.location.href = `/login?next_page=${window.location.href}`
                                }, "Login"
                            );
                        } else {
                            const body = await response.json();
                            console.log(JSON.stringify(body));
                            showNotification(body.detail, "error");
                        }
                    }
                } catch (error) {
                    setEndorsementRequest(null);
                    setEndorsee(null);
                    showNotification(JSON.stringify(error), "error");
                }
            }
        }

        findEndorsementRequest();

        if (!endorsementCodeValidator(formData?.endorsement_code)) {
            setEndorsementRequest(null);
            setEndorsee(null);
        }
    }, [formData.endorsement_code]);


    useEffect(() => {
        if (endorsementRequest) {
            async function findEndorsee() {
                if (endorsementRequest) {
                    try {
                        const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/public-users/?user_id=${endorsementRequest?.endorsee_id}`);
                        if (response.ok) {
                            const body: PublicUserType = await response.json();
                            setErrors({...errors, endorsee: ""});
                            setEndorsee(body);
                        } else {
                            if (response.status === 404) {
                                setErrors({...errors, endorsee: "Cannot find endorsee"});
                            }
                            const body = await response.json();
                            showNotification(body.detail, "error");
                            setEndorsee(null);
                        }
                    } catch (error) {
                        showNotification(String(error) || "Cannot find endorsee", "error");
                        setEndorsee(null);
                    }
                }
            }

            findEndorsee();
        }
    }, [endorsementRequest]);


    useEffect(() => {
        if (endorsementRequest) {
            async function getCategoryName() {
                if (endorsementRequest) {
                    try {
                        const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/categories/${endorsementRequest?.archive}/subject-class/${endorsementRequest?.subject_class}`);
                        if (response.ok) {
                            const body: CategoryResponse = await response.json();
                            setEndorsementCategoryName(body.category_name);
                        } else {
                            setEndorsementCategoryName(null);
                        }
                    } catch (error) {
                        setEndorsementCategoryName(null);
                    }
                }
            }

            getCategoryName();
        }
    }, [endorsementRequest]);


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        setInProgress(true);
        event.preventDefault();

        try {
            const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/endorsements/endorse", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const errorReply = await response.json();
                console.error(response.statusText);
                console.log(JSON.stringify(errorReply));
                if (response.status === 405) {
                    const outcome = errorReply as unknown as Endorsement405Response;
                    showMessageDialog(outcome.reason, "Endorsement failed");
                } else {
                    showNotification(errorReply.detail, "warning");
                }
                return;
            }

            if (response.status === 200) {
                showNotification("Endorsement complete", "success");
                return;
            }
            const body = await response.json();
            showNotification(`Unexpected respones ${response.statusText} -  ${body.detail}`, "warning");
        } catch (error) {
            console.error("Error:", error);
            showNotification(JSON.stringify(error), "warning");
        } finally {
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
        } else if (type === "radio") {
            setFormData({
                ...formData,
                [name]: value === "true",
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


    function printUser(user: PublicUserType | User | null): string {
        if (!user)
            return "";
        const maybe_email = user?.email ? ` <${user?.email}>` : '';
        return `${user?.first_name} ${user?.last_name}${maybe_email} - ${user?.affiliation || "No affiliation"}`;
    }

    function printUserName(user: PublicUserType | User | null): string {
        if (!user)
            return "";
        return `${user?.first_name} ${user?.last_name}`;
    }

    function printCategory(endoresementRequest: EndorsementRequestType | null): string {
        if (!endoresementRequest)
            return "";
        return `${endoresementRequest?.archive}${endoresementRequest?.subject_class ? "." + endoresementRequest.subject_class : ""}`;
    }

    const categoryFullName = endorsementRequest ? `${printCategory(endorsementRequest)} - ${endorsementCategoryName}` : "";

    const endorsementLabel = endorsementRequest ? (
        <CardHeader title={`Endorsement of ${printUserName(endorsee)} for ${categoryFullName}`} />
    ) : null;

    const endorserInfo = endorsementRequest ? (<Typography >
            <Typography component={"span"} fontWeight={"bold"}> {"Endorser (You): "}</Typography>
            <Typography component={"span"}
                        sx={{textDecoration: "underline"}}>{printUser(user)}</Typography>
        </Typography>
    ) : null;

    const endorseeInfo = endorsee ? (
        <Typography >
            <Typography>
                The following has requested your endorsement to submit papers to {printCategory(endorsementRequest)}
                {" ("}{endorsementCategoryName}). Your publication history is sufficient to endorse this user.
            </Typography>
            <Box sx={{height: "8px"}} />
            <Typography component={"span"} fontWeight={"bold"}>{"Endorsement: "}</Typography>
            <Typography component={"span"}
                        sx={{textDecoration: "underline"}}> {printUser(endorsee)}</Typography>
            {" for category "}
            <Typography component={"span"} sx={{textDecoration: "underline"}}>{printCategory(endorsementRequest)}</Typography>

        </Typography>
    ) : null;

    const endorsementSelection = endorsementRequest ? (
        <Box>
            <Typography component={"li"}>
                You can endorse {printUserName(endorsee)}.
            </Typography>
            <Typography component={"li"}>
                You can tell us that you don't want to endorse {printUserName(endorsee)}.
            </Typography>
            <Typography component={"li"}>
                Do nothing.
            </Typography>

            <FormControl component="fieldset"
                         disabled={errors?.endorsement_code ? true : false}>
                <RadioGroup
                    tabIndex={2}
                    name="positive"
                    id="positive"
                    value={formData.positive ? "true" : "false"}
                    onChange={handleChange}
                >
                    <Box sx={{
                        display: "flex",
                        flexDirection: "row",
                        gap: 2,
                        alignItems: "center",
                        ml: 3,
                        mt: 1
                    }}>
                        <FormControlLabel tabIndex={3} value="true" control={<Radio/>}
                                          label={`Endorse ${printUserName(endorsee)}`}/>
                        <FormControlLabel tabIndex={4} value="false" control={<Radio/>}
                                          label={`Wish to not endorse ${printUserName(endorsee)}`}/>
                    </Box>
                </RadioGroup>
            </FormControl>
        </Box>
    ) : null;

    const choices = endorsementRequest ? (
        <>
            <Box sx={{display: "flex", flexDirection: "row", gap: 2, alignItems: "center"}}>
                <FormControlLabel tabIndex={5}
                                  control={<Checkbox name="seen_paper" id="seen_paper" key={"seen_paper"}
                                                     onChange={handleChange}/>} label={"Seen paper"}/>
                <FormControlLabel tabIndex={6}
                                  control={<Checkbox name="knows_personally" id="knows_personally"
                                                     key={"knows_personally"} onChange={handleChange}/>}
                                  label={"Knows personally"}/>
            </Box>
        <Box>
            <Typography component="span"  >
                <Typography fontWeight={"bold"}>{"Comment: "}</Typography>
                <Typography >{" (Optional) Enter any comments on why you would or would not endorse "}{printUserName(endorsee)}</Typography>
            </Typography>
            <TextField name="comment" id="comment" label="Comment" multiline
                       variant="outlined" fullWidth onChange={handleChange}
                       error={Boolean(errors.comment)} helperText={errors.comment}
                       sx={{mt: 1}}
                       minRows={4} tabIndex={7}
            />
        </Box>

    <Box display="flex" justifyContent="space-between" alignItems="center">
        <Button type="submit" variant="contained" tabIndex={8} sx={{
            backgroundColor: "#1976d2",
            "&:hover": {
                backgroundColor: "#1420c0"
            }
        }} disabled={invalidFormData || inProgress}>
            Submit
        </Button>
    </Box>
        </>
    ) : null;


    return (
        <Container maxWidth="md" sx={{mt: 2}}>
            <Typography variant={"h5"}>Login to arXiv.org </Typography>

            {/* Endorse Form */}
            <Card elevation={0}
                  sx={{
                      p: 2,
                      position: 'relative',
                      paddingTop: '48px', // Add padding to push content down
                      paddingBottom: '48px', // Add padding to push content down
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
                        Endorsement
                    </Typography>
                </Box>
                {endorsementLabel}
                <CardContent>
                    <Box component="form" sx={{display: "flex", flexDirection: "column", gap: 2}}
                         onSubmit={handleSubmit}>
                        <input name="user_id" id="user_id" type="text" disabled={true} value={formData.endorser_id}
                               hidden={true}/>
                        <Box sx={{display: "flex", flexDirection: "row", gap: 2, alignItems: "center"}}>
                            <Box>
                                <Typography fontWeight={"bold"}
                                            sx={{mb: 1}}>{"Endorsement code"}</Typography>
                                <Box>
                                    <TextField tabIndex={1}
                                               sx={{width: "10em"}}
                                               name="endorsement_code" id="endorsement_code" label="Endorsement code"
                                               variant="outlined" onChange={handleChange}
                                               value={formData.endorsement_code}
                                               error={Boolean(errors.endorsement_code)}
                                               helperText={errors.endorsement_code}/>
                                </Box>
                            </Box>
                        </Box>

                        {endorserInfo}
                        {endorseeInfo}

                        {endorsementSelection}
                        {choices}
                    </Box>
                </CardContent>
            </Card>
        </Container>
    );
};

export default EnterEndorsementCode;