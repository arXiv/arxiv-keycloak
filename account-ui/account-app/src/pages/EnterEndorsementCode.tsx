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
import Link from "@mui/material/Link";
import {printUserName} from "../bits/printer.ts";
import {useFetchPlus} from "../fetchPlus.ts";

type EndorsementCodeRequest = adminApi["/v1/endorsements/endorse"]['post']['requestBody']['content']['application/json'];

type EndorsementOutcomeModel = adminApi["/v1/endorsements/endorse"]['post']['responses']['200']['content']['application/json'];
type Endorsement405Response = adminApi["/v1/endorsements/endorse"]['post']['responses']['405']['content']['application/json'];
type EndorsementRequestType = adminApi["/v1/endorsement_requests/code"]['get']['responses']['200']['content']['application/json'];
type PublicUserType = EndorsementOutcomeModel["endorsee"];
type CategoryResponse = adminApi["/v1/categories/{archive}/subject-class/{subject_class}"]['get']['responses']['200']['content']['application/json'];


const EnterEndorsementCode = () => {
    const runtimeProps = useContext(RuntimeContext);
    const user = runtimeProps.currentUser;
    const {showNotification, showMessageDialog} = useNotification();
    const [inProgress, setInProgress] = useState(false);
    const [endorsementOutcome, setEndorsementOutcome] = useState<EndorsementOutcomeModel | null>(null);
    const [endorsementCategoryName, setEndorsementCategoryName] = useState<string | null>(null);
    const endorsementRequest = endorsementOutcome?.endorsement_request
    const endorsee = endorsementOutcome?.endorsee;
    const categoryName = endorsementRequest ? `${printCategory(endorsementRequest)}` : "";
    const categoryFullName = endorsementRequest ? `${printCategory(endorsementRequest)} - ${endorsementCategoryName}` : "";
    const initialFormData: EndorsementCodeRequest = {
        preflight: true,
        endorser_id: user?.id || "",
        positive: true,
        endorsement_code: "",
        comment: "",
        knows_personally: false,
        seen_paper: false
    };
    const [formData, setFormData] = useState<EndorsementCodeRequest>(initialFormData);

    const [errors, setErrors] = useState<{
        endorser_id?: string,
        positive?: boolean,
        endorsement_code?: string,
        comment?: string,
        knows_personally?: string,
        seen_paper?: string,
        endorsee?: string,
        reason?: string
    }>({endorser_id: "No current user", endorsement_code: "Empty"});

    const fetchPlus = useFetchPlus();


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
            if (formData?.endorsement_code && formData?.preflight) {
                const query = new URLSearchParams();
                query.set("secret", formData.endorsement_code);
                try {
                    const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + '/endorsements/endorse',
                        {
                            method: "POST",
                            body: JSON.stringify(formData),
                            headers: new Headers({"Content-Type": "application/json",
                            })},);
                    if (response.ok) {
                        setErrors({...errors, endorsement_code: ""});
                        const body: EndorsementOutcomeModel = await response.json();
                        setEndorsementOutcome(body);
                    } else {
                        setEndorsementOutcome(null);
                        if (response.status === 404) {
                            setErrors({...errors, endorsement_code: "Not Found"});
                        }
                        else if (response.status === 401) {
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
                    setEndorsementOutcome(null);
                    showNotification(JSON.stringify(error), "error");
                }
            }
        }

        findEndorsementRequest();

        if (!endorsementCodeValidator(formData?.endorsement_code)) {
            setEndorsementOutcome(null);
        }
    }, [formData.endorsement_code]);


    useEffect(() => {
        async function getCategoryName() {
            const er = endorsementOutcome?.endorsement_request;
            if (er) {
                try {
                    const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + `/categories/${er.archive}/subject-class/${er.subject_class}`);
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

        if (endorsementOutcome?.endorsement_request) {
            getCategoryName();
        }
    }, [endorsementOutcome]);

    function printUser(user: PublicUserType | User | null): string {
        if (!user)
            return "";
        const maybe_email = user?.email ? ` <${user?.email}>` : '';
        return `${user?.first_name} ${user?.last_name}${maybe_email} - ${user?.affiliation || "No affiliation"}`;
    }

    function printCategory(endoresementRequest: EndorsementRequestType | null): string {
        if (!endoresementRequest)
            return "";
        return `${endoresementRequest?.archive}${endoresementRequest?.subject_class ? "." + endoresementRequest.subject_class : ""}`;
    }


    const endorseeName = printUserName(endorsee);
    const endorser_name = printUser(user);

    // When the outcome shows up, do something
    useEffect(() => {
        if (!endorsementOutcome) return;
        const email = runtimeProps.URLS.arxivAdminContactEmail;
        const emailLink = (<Link href={`email:${email}`}>{email}</Link>);

        if (endorsementOutcome.submitted) {
            const feedback = endorsementOutcome.endorsement?.point_value ? "endorse" : "not endorse";
            const title = `You've already decided to ${feedback} ${endorseeName}`;
            const msg = (<div>
                <p>You've already decided to {feedback} {endorseeName} for the
                    {categoryFullName}</p>
                <p>arXiv users are
                    allowed to endorse (or not endorse) a user for a particular archive or
                    subject class only once.
                </p>
                <p>Thank you for helping us maintain the quality of arXiv submissions.
                    If you've made a terrible mistake or if you have any questions or comments,
                    contact {emailLink}.</p>
            </div>);
            showMessageDialog(msg, title);
        }
        else if (endorsementOutcome.endorser_capability === "credited" && endorsementOutcome.request_acceptable) {
            setErrors({...errors, reason: ""});
        } else if (endorsementOutcome.endorser_capability === "prohibited") {
            setErrors({...errors, reason: endorsementOutcome?.reason || "You may not endorse."});
            const not_ok = (<p>Your ability to endorse other arXiv users has been suspended
                by administrative action. If you believe this is a mistake, please
                contact {emailLink}.</p>);
            showMessageDialog(not_ok, "You are not allowed to endorse");
        } else if (endorsementOutcome.endorser_capability === "uncredited") {
            setErrors({...errors, reason: endorsementOutcome?.reason || "You are not qualified to endorse."});

            const title = `You are not allowed to endorse for ${categoryName}`;
            const msg = (<div>
                <p>You are not allowed to endorse arXiv users for category {categoryFullName}
                    {endorsementOutcome?.reason ? ` for the following reason: ${endorsementOutcome.reason}` : ""}.
                </p>
                <p>Please advise {endorseeName} to find another endorser. Please contact {emailLink} if you have any questions or comments.</p>
            </div>);
            showMessageDialog(msg, title);
        } else if (endorsementOutcome.endorser_capability === "oneself") {
            setErrors({...errors, reason: endorsementOutcome?.reason || "You cannot endorse yourself."});

            const title = "You cannot endorse yourself";
            const msg = (<div>
                <p>People cannot endorse themselves. You must find somebody else to
                    give you an endorsement. If you think that you have received this
                    message in error or need help, please contact {emailLink}.</p>
            </div>);
            showMessageDialog(msg, title,
                () => setFormData(initialFormData), "Understood");
        } else {
            setErrors({...errors, reason: endorsementOutcome?.reason || "Reason is not given."});
        }

    }, [endorsementOutcome]);


    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        setInProgress(true);
        event.preventDefault();

        try {
            const response = await fetchPlus(runtimeProps.ADMIN_API_BACKEND_URL + "/endorsements/endorse", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({...formData, preflight: false}),
            });

            if (!response.ok) {
                const errorReply = await response.json();
                console.error(response.statusText);
                console.log(JSON.stringify(errorReply));
                if (response.status === 405) {
                    const outcome = errorReply as unknown as Endorsement405Response;
                    showMessageDialog((<span>{outcome?.reason  || "Reason not given"}</span>), "Endorsement failed");
                } else {
                    showNotification(errorReply.detail, "warning");
                }
                return;
            }

            if (response.status === 200) {
                const body: EndorsementOutcomeModel = await response.json();
                if (body.endorsement?.point_value) {
                    showMessageDialog(
                        (<>
                            <p>Your endorsement helps us maintain the quality of arXiv submissions.</p>
                            <p>{`${endorseeName} is now authorized to upload articles to ${categoryFullName}.; `}
                                {`we've informed ${endorseeName} of this by sending an e-mail. (We did not tell ${endorseeName} that the endorsement came from you.)`}</p>
                        </>),
                        `Thank you for endorsing ${endorseeName}`
                        , () => setFormData(initialFormData), "Restart");
                }
                else {
                    showMessageDialog(
                        (<>
                            <p>Your vigilance helps us maintain the quality of arXiv submissions.</p>

                            <p>Your vote of no confidence will not result in any automatic action against {endorseeName};
                                {endorseeName} will still be able to submit to the {categoryName} if they can find another
                                endorser.  However, your feedback may help us detect massive abuse (users
                                who contact hundreds of arXiv users in the hope of finding someone who'll
                                endorse them without thinking) and will direct our attention to possible
                                problem submissions.</p>

                            <p>{endorseeName} will not be informed of your feedback.  It is your
                                responsibility to tell (or not tell) {endorseeName} of your decision.</p>
                        </>),
                        `Thank you for your feedback on ${endorseeName}`
                        , () => setFormData(initialFormData), "Restart");

                }
                return;
            }
            else {
                const body = await response.json();
                showNotification(`Unexpected respones ${response.statusText} -  ${body.detail}`, "warning");
            }
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
            if (value === "undefined") {
                setFormData({
                    ...formData,
                    [name]: undefined,
                })
            }
            else {
                setFormData({
                    ...formData,
                    [name]: value === "true",
                })
            }
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

    const endorsementLabel = endorsementRequest && endorsee ? (
        <CardHeader title={`Endorsement of ${endorseeName} for ${categoryFullName}`} />
    ) : null;

    const endorserInfo = (<Typography >
            <Typography component={"span"} fontWeight={"bold"}> {"Endorser (You): "}</Typography>
            <Typography component={"span"}
                        sx={{textDecoration: "underline"}}>{endorser_name}</Typography>
        </Typography>
    );

    const endorseeInfo = endorsee && endorsementRequest ? (
        <Typography >
            <Typography component="p" >
                {endorseeName} has requested your endorsement to submit papers to {printCategory(endorsementRequest)}
                {" ("}{endorsementCategoryName}).
            </Typography>
            <Typography component="p" sx={{p:2}}>
                { endorsementOutcome?.request_acceptable ?
                    (
                        <Typography>
                            Acceptance reason:
                            <Typography>{endorsementOutcome?.reason || "Endorsement request is valid."}</Typography>
                        </Typography>
                    )
                    :
                    (
                        <Typography>
                            Reject reason:
                            <Typography sx={{fontStyle: "italic"}}>{endorsementOutcome.reason || "Endorsee cannot receive any endorsement."}</Typography>
                        </Typography>
                    )
                }
            </Typography>
            <Typography component={"span"} fontWeight={"bold"}>{"Endorsement: "}</Typography>
            <Typography component={"span"}
                        sx={{textDecoration: "underline"}}> {printUser(endorsee)}</Typography>
            {" for category "}
            <Typography component={"span"} sx={{textDecoration: "underline"}}>{printCategory(endorsementRequest)}</Typography>

        </Typography>
    ) : null;

    const ok_to_submit = endorsementRequest && endorsementOutcome?.request_acceptable && endorsementOutcome.endorser_capability === "credited";

    const endorsementSelection = ok_to_submit ? (
        <Box>
            <Typography sx={{fontWeight: "bold"}}>
                arXiv will only inform {endorseeName} if you choose to endorse.
            </Typography>
            <FormControl component="fieldset"
                         disabled={errors?.endorsement_code?.length ? true : false}>
                <RadioGroup
                    tabIndex={2}
                    name="positive"
                    id="positive"
                    value={formData.positive ? "true" : "false"}
                    onChange={handleChange}
                >
                        <FormControlLabel tabIndex={3} value="true" control={<Radio/>}
                                          label={`Endorse ${endorseeName} (Allow submitting to category)`}/>
                        <FormControlLabel tabIndex={4} value="false" control={<Radio/>}
                                          label={`Deny ${endorseeName} (Vote of no confidence, do not allow submitting to category)`}/>
                        <FormControlLabel tabIndex={5} value="undefined" control={<Radio/>}
                                          label={"I don't know."}/>

                </RadioGroup>
            </FormControl>
        </Box>
    ) : null;

    const choices = ok_to_submit ? (
        <>
            <Box sx={{display: "flex", flexDirection: "row", gap: 2, alignItems: "center"}}>
                <FormControlLabel tabIndex={6}
                                  control={<Checkbox name="seen_paper" id="seen_paper" key={"seen_paper"}
                                                     onChange={handleChange}/>} label={"Seen paper"}/>
                <FormControlLabel tabIndex={7}
                                  control={<Checkbox name="knows_personally" id="knows_personally"
                                                     key={"knows_personally"} onChange={handleChange}/>}
                                  label={"Knows personally"}/>
            </Box>
        <Box>
            <Typography component="span"  >
                <Typography fontWeight={"bold"}>{"Comment: "}</Typography>
                <Typography >{" (Optional) Enter any comments on why you would or would not endorse "}{endorseeName}</Typography>
            </Typography>
            <TextField name="comment" id="comment" label="Comment" multiline
                       variant="outlined" fullWidth onChange={handleChange}
                       error={Boolean(errors.comment)} helperText={errors.comment}
                       sx={{mt: 1}}
                       minRows={4} tabIndex={8}
            />
        </Box>

    <Box display="flex" justifyContent="space-between" alignItems="center">
        <Button type="submit" variant="contained" tabIndex={8} sx={{
            backgroundColor: "#1976d2",
            "&:hover": {
                backgroundColor: "#1420c0"
            }
        }} disabled={inProgress}>
            Cancel
        </Button>

        <Button type="submit" variant="contained" tabIndex={9} sx={{
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

                        {endorseeInfo}

                        {endorserInfo}

                        {endorsementSelection}
                        {choices}
                    </Box>
                </CardContent>
            </Card>
        </Container>
    );
};

export default EnterEndorsementCode;