import React, {useContext, useEffect, useState} from "react";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Container from "@mui/material/Container";
import Stepper from "@mui/material/Stepper";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import StepContent from "@mui/material/StepContent";
import Paper from "@mui/material/Paper";

import {RuntimeContext, User} from "../RuntimeContext";
import {useNotification} from "../NotificationContext";

import {paths as adminApi} from "../types/admin-api";
import {endorsementCodeValidator} from "../bits/validators";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import RadioGroup from "@mui/material/RadioGroup";
import Radio from "@mui/material/Radio";
import CardHeader from "@mui/material/CardHeader";
import Link from "@mui/material/Link";
import {printUserName} from "../bits/printer.ts";
import {useLocation} from "react-router-dom";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import {
    ADMIN_CATEGORY_ARCHIVE_SUBJECT_CLASS_URL,
    ADMIN_ENDORSEMENT_ENDORSE_URL,
    ADMIN_ENDORSEMENT_REQUESTS_CODE
} from "../types/admin-url.ts";

type EndorsementCodeRequest = adminApi[typeof ADMIN_ENDORSEMENT_ENDORSE_URL]['post']['requestBody']['content']['application/json'];

type EndorsementOutcomeModel = adminApi[typeof ADMIN_ENDORSEMENT_ENDORSE_URL]['post']['responses']['200']['content']['application/json'];
type Endorsement405Response = adminApi[typeof ADMIN_ENDORSEMENT_ENDORSE_URL]['post']['responses']['405']['content']['application/json'];
type EndorsementRequestType = adminApi[typeof ADMIN_ENDORSEMENT_REQUESTS_CODE]['get']['responses']['200']['content']['application/json'];
type PublicUserType = EndorsementOutcomeModel["endorsee"];
type CategoryResponse = adminApi[typeof ADMIN_CATEGORY_ARCHIVE_SUBJECT_CLASS_URL]['get']['responses']['200']['content']['application/json'];

const steps = [
    'Enter Endorsement Code',
    'Review Endorsement Details',
    'Make Endorsement Decision',
    'Complete Endorsement'
];

const EndorsementStepper = () => {
    const runtimeProps = useContext(RuntimeContext);
    const location = useLocation();
    const user = runtimeProps.currentUser;
    const {showNotification, showMessageDialog} = useNotification();
    const [activeStep, setActiveStep] = useState(0);
    const [inProgress, setInProgress] = useState(false);
    const [endorsementOutcome, setEndorsementOutcome] = useState<EndorsementOutcomeModel | null>(null);
    const [endorsementCategoryName, setEndorsementCategoryName] = useState<string | null>(null);
    const endorsementRequest = endorsementOutcome?.endorsement_request
    const endorsee = endorsementOutcome?.endorsee;
    const categoryName = endorsementRequest ? `${printCategory(endorsementRequest)}` : "";
    const categoryFullName = endorsementRequest ? `${printCategory(endorsementRequest)} - ${endorsementCategoryName || "all"}` : "";

    const queryParams = new URLSearchParams(location.search);
    const codeFromURL = queryParams.get("code") || "";

    const initialFormData: EndorsementCodeRequest = {
        preflight: true,
        endorser_id: user?.id || "",
        positive: true,
        endorsement_code: codeFromURL,
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
    }>({endorser_id: "No current user", endorsement_code: codeFromURL ? "" : "Empty"});

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
                    const postEndorsement = runtimeProps.adminFetcher.path(ADMIN_ENDORSEMENT_ENDORSE_URL).method('post').create();
                    const response = await postEndorsement(formData);

                    if (response.ok) {
                        setErrors({...errors, endorsement_code: ""});
                        const body: EndorsementOutcomeModel = response.data;
                        setEndorsementOutcome(body);
                        // Auto-advance to next step if code is valid
                        if (activeStep === 0) {
                            setActiveStep(1);
                        }
                    } else {
                        setEndorsementOutcome(null);
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
                            const errorMessage = (response.data as any)?.detail || "Unknown error";
                            console.log(JSON.stringify(response.data));
                            showNotification(errorMessage, "error");
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
                    const getCategoryInfo = runtimeProps.adminFetcher.path(ADMIN_CATEGORY_ARCHIVE_SUBJECT_CLASS_URL).method('get').create();
                    const response = await getCategoryInfo({archive: er.archive || '', subject_class: er.subject_class || ''});
                    if (response.ok) {
                        const body: CategoryResponse = response.data;
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
        } else if (endorsementOutcome.endorser_capability === "credited" && endorsementOutcome.request_acceptable) {
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
                <p>Please advise {endorseeName} to find another endorser. Please contact {emailLink} if you have any
                    questions or comments.</p>
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
                () => {
                    setFormData(initialFormData);
                    setActiveStep(0);
                }, "Understood");
        } else {
            setErrors({...errors, reason: endorsementOutcome?.reason || "Reason is not given."});
        }

    }, [endorsementOutcome]);

    const handleSubmit = async () => {
        setInProgress(true);

        try {
            const postEndorsement = runtimeProps.adminFetcher.path(ADMIN_ENDORSEMENT_ENDORSE_URL).method('post').create();
            const response = await postEndorsement({...formData, preflight: false});

            if (!response.ok) {
                const errorReply = response.data;
                console.error(response.statusText);
                console.log(JSON.stringify(errorReply));
                if (response.status === 405) {
                    const outcome = errorReply as unknown as Endorsement405Response;
                    showMessageDialog((<span>{outcome?.reason || "Reason not given"}</span>), "Endorsement failed");
                } else {
                    const errorMessage = (errorReply as any)?.detail || "Unknown error";
                    showNotification(errorMessage, "warning");
                }
                return;
            }

            if (response.status === 200) {
                const body: EndorsementOutcomeModel = response.data;
                if (body.endorsement?.point_value) {
                    showMessageDialog(
                        (<>
                            <p>Your endorsement helps us maintain the quality of arXiv submissions.</p>
                            <p>{`${endorseeName} is now authorized to upload articles to ${categoryFullName}.; `}
                                {`we've informed ${endorseeName} of this by sending an e-mail. (We did not tell ${endorseeName} that the endorsement came from you.)`}</p>
                        </>),
                        `Thank you for endorsing ${endorseeName}`
                        , () => {
                            setFormData(initialFormData);
                            setActiveStep(0);
                        }, "Restart");
                } else {
                    showMessageDialog(
                        (<>
                            <p>Your vigilance helps us maintain the quality of arXiv submissions.</p>

                            <p>Your vote of no confidence will not result in any automatic action against {endorseeName};
                                {endorseeName} will still be able to submit to the {categoryName} if they can find
                                another
                                endorser. However, your feedback may help us detect massive abuse (users
                                who contact hundreds of arXiv users in the hope of finding someone who'll
                                endorse them without thinking) and will direct our attention to possible
                                problem submissions.</p>

                            <p>{endorseeName} will not be informed of your feedback. It is your
                                responsibility to tell (or not tell) {endorseeName} of your decision.</p>
                        </>),
                        `Thank you for your feedback on ${endorseeName}`
                        , () => {
                            setFormData(initialFormData);
                            setActiveStep(0);
                        }, "Restart");

                }
                return;
            } else {
                const errorMessage = (response.data as any)?.detail || "Unknown error";
                showNotification(`Unexpected response ${response.statusText} - ${errorMessage}`, "warning");
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
            } else {
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

    const handleNext = () => {
        setActiveStep((prevActiveStep) => prevActiveStep + 1);
    };

    const handleBack = () => {
        setActiveStep((prevActiveStep) => prevActiveStep - 1);
    };

    const handleReset = () => {
        setActiveStep(0);
        setFormData(initialFormData);
        setEndorsementOutcome(null);
        setEndorsementCategoryName(null);
    };

    const invalidFormData = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );

    const ok_to_submit = endorsementRequest && endorsementOutcome?.request_acceptable && endorsementOutcome.endorser_capability === "credited";

    const getStepContent = (step: number) => {
        switch (step) {
            case 0:
                return (
                    <Box sx={{display: "flex", flexDirection: "column", gap: 2}}>
                        <TextField
                            name="endorsement_code"
                            id="endorsement_code"
                            label="Endorsement code"
                            onChange={handleChange}
                            value={formData.endorsement_code}
                            error={Boolean(errors.endorsement_code)}
                            helperText={errors.endorsement_code}
                            fullWidth
                        />
                    </Box>
                );
            case 1:
                return (
                    <Box sx={{display: "flex", flexDirection: "column", gap: 2}}>
                        <Typography variant="h6">Endorser (You):</Typography>
                        <Typography sx={{textDecoration: "underline"}}>{endorser_name}</Typography>

                        {endorsee && endorsementRequest && (
                            <Box>
                                <Typography variant="h6">Endorsement Request:</Typography>
                                <Typography>
                                    {endorseeName} has requested your endorsement to submit papers to {printCategory(endorsementRequest)}
                                    {" ("}{endorsementCategoryName}).
                                </Typography>
                                <Typography sx={{p: 2}}>
                                    {endorsementOutcome?.request_acceptable ?
                                        (<Typography>
                                            Acceptance reason:
                                            <Typography>{endorsementOutcome?.reason || "Endorsement request is valid."}</Typography>
                                        </Typography>)
                                        :
                                        (<Typography>
                                            Reject reason:
                                            <Typography sx={{fontStyle: "italic"}}>
                                                {endorsementOutcome.reason || "Endorsee cannot receive any endorsement."}
                                            </Typography>
                                        </Typography>)
                                    }
                                </Typography>
                                <Typography sx={{fontWeight: "bold"}}>Endorsee: </Typography>
                                <Typography sx={{textDecoration: "underline"}}> {printUser(endorsee)}</Typography>
                                {" for category "}
                                <Typography sx={{textDecoration: "underline"}}>{printCategory(endorsementRequest)}</Typography>
                            </Box>
                        )}
                    </Box>
                );
            case 2:
                return (
                    <Box sx={{display: "flex", flexDirection: "column", gap: 2}}>
                        <Typography sx={{fontWeight: "bold"}}>
                            arXiv will only inform {endorseeName} if you choose to endorse.
                        </Typography>
                        <FormControl component="fieldset" disabled={!!errors?.endorsement_code?.length}>
                            <RadioGroup
                                name="positive"
                                id="positive"
                                value={formData.positive ? "true" : "false"}
                                onChange={handleChange}
                            >
                                <FormControlLabel value="true" control={<Radio/>}
                                                  label={`Endorse ${endorseeName} (Allow submitting to category)`}/>
                                <FormControlLabel value="false" control={<Radio/>}
                                                  label={`Deny ${endorseeName} (Vote of no confidence, do not allow submitting to category)`}/>
                            </RadioGroup>
                        </FormControl>
                    </Box>
                );
            case 3:
                return (
                    <Box sx={{display: "flex", flexDirection: "column", gap: 2}}>
                        <Box sx={{display: "flex", flexDirection: "row", gap: 2, alignItems: "center"}}>
                            <FormControlLabel
                                control={<Checkbox name="seen_paper" id="seen_paper" onChange={handleChange}/>}
                                label={"Seen paper"}/>
                            <FormControlLabel
                                control={<Checkbox name="knows_personally" id="knows_personally" onChange={handleChange}/>}
                                label={"Knows personally"}/>
                        </Box>
                        <TextField
                            name="comment"
                            id="comment"
                            label="Comment: (Optional) Enter any comments on why you would or would not endorse "
                            multiline
                            fullWidth
                            onChange={handleChange}
                            error={Boolean(errors.comment)}
                            helperText={errors.comment}
                            minRows={4}
                        />
                    </Box>
                );
            default:
                return 'Unknown step';
        }
    };

    return (
        <Container maxWidth={"md"} sx={{mt: 2}}>
            <Box display="flex" flexDirection={"column"} sx={{my: "2em"}}>
                <Typography variant={"h1"}>
                    Giving an endorsement
                </Typography>

                <CardWithTitle title={"Endorsing"}>
                    {endorsementRequest && endorsee && (
                        <CardHeader title={`Endorsement of ${endorseeName} for ${categoryFullName}`}/>
                    )}

                    <Stepper activeStep={activeStep} orientation="vertical">
                        {steps.map((label, index) => (
                            <Step key={label}>
                                <StepLabel>{label}</StepLabel>
                                <StepContent>
                                    {getStepContent(index)}
                                    <Box sx={{mb: 2}}>
                                        <div>
                                            {index === steps.length - 1 ? (
                                                <Button
                                                    variant="contained"
                                                    onClick={handleSubmit}
                                                    disabled={invalidFormData || inProgress || !ok_to_submit}
                                                    sx={{mt: 1, mr: 1}}
                                                >
                                                    Submit Endorsement
                                                </Button>
                                            ) : (
                                                <Button
                                                    variant="contained"
                                                    onClick={handleNext}
                                                    disabled={
                                                        (index === 0 && !endorsementOutcome) ||
                                                        (index === 1 && !ok_to_submit)
                                                    }
                                                    sx={{mt: 1, mr: 1}}
                                                >
                                                    Continue
                                                </Button>
                                            )}
                                            <Button
                                                disabled={index === 0}
                                                onClick={handleBack}
                                                sx={{mt: 1, mr: 1}}
                                            >
                                                Back
                                            </Button>
                                        </div>
                                    </Box>
                                </StepContent>
                            </Step>
                        ))}
                    </Stepper>

                    {activeStep === steps.length && (
                        <Paper square elevation={0} sx={{p: 3}}>
                            <Typography>Endorsement completed!</Typography>
                            <Button onClick={handleReset} sx={{mt: 1, mr: 1}}>
                                Start New Endorsement
                            </Button>
                        </Paper>
                    )}
                </CardWithTitle>
            </Box>
        </Container>
    );
};

export default EndorsementStepper;