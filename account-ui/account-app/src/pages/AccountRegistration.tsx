import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import Checkbox from "@mui/material/Checkbox";
import Link from "@mui/material/Link";
import Dialog from "@mui/material/Dialog";
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';

import React, {useCallback, useContext, useEffect, useState} from "react";
// import CountrySelector from "../bits/CountrySelector.tsx";
// import CareerStatusSelect, {CareerStatusType} from "../bits/CareerStatus.tsx";
import {RuntimeContext} from "../RuntimeContext.tsx";
import {paths} from "../types/aaa-api.ts";
import RefreshIcon from "@mui/icons-material/Refresh";
import HearingIcon from "@mui/icons-material/Hearing";
import LinkIcon from "@mui/icons-material/Launch";
import {emailValidator, passwordValidator} from "../bits/validators.ts";
import {useNotification} from "../NotificationContext.tsx";

import CardWithTitle from "../bits/CardWithTitle.tsx";
import FormControlLabel from "@mui/material/FormControlLabel";

// import {useTheme} from "@mui/material";
import TextField from "@mui/material/TextField";
import LineDivider from "../bits/LineDevider.tsx";
import PasswordWrapper from "../bits/PasswordWrapper.tsx";
import PasswordRequirements from "../bits/PasswordRequirements.tsx";
import UserInfoForm from "./demographic/UserInfoForm.tsx";
import {AccountFormError} from "./demographic/AccountFormError.ts";
import SubmissionCategoryForm from "./demographic/SubmissionCategoryForm.tsx";
import {ACCOUNT_REGISTER_PREFLIGHT_URL, ACCOUNT_REGISTER_URL} from "../types/aaa-url.ts";
/* import IconButton from '@mui/material/IconButton';
import Collapse from '@mui/material/Collapse';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AccentedCharactersGuide from "../bits/AccentedChars.tsx";

 */
type TokenResponse = paths[typeof ACCOUNT_REGISTER_URL]['get']['responses']['200']['content']['application/json'];
type SubmitRequest = paths[typeof ACCOUNT_REGISTER_URL]['post']['requestBody']['content']['application/json'];
// type RegistrationSuccessReply = paths["/account/register/"]['post']['responses']['200']['content']['application/json'];
type RegistrationErrorReply = paths[typeof ACCOUNT_REGISTER_URL]['post']['responses']['400']['content']['application/json'];

interface PostSubmitDialogProps {
    title: string;
    message: string;
    open: boolean;
    onClose?: () => void;
    onConfirm?: () => void;
}

const PostSubmitActionDialog: React.FC<PostSubmitDialogProps> = ({title, message, open, onClose, onConfirm}) => {
    return (
        <Dialog open={open} onClose={onClose}>
            <DialogTitle>{title}</DialogTitle>
            <DialogContent>
                <Typography>{message}</Typography>
            </DialogContent>
            <DialogActions>
                {
                    onClose ? <Button onClick={onClose} color="secondary">Cancel</Button> : null
                }
                {
                    onConfirm ? <Button onClick={onConfirm} color="secondary">Okay</Button> : null
                }
            </DialogActions>
        </Dialog>
    );
}

const FlexOne = () => <Box sx={{flex: 1}} />


const AccountRegistration = () => {
    const runtimeContext = useContext(RuntimeContext);
    const {showNotification} = useNotification();
    // const theme = useTheme();
    // const [expanded, setExpanded] = useState(false);

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
        career_status: "Unknown",
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

    const [errors, setErrors] = useState<AccountFormError>({
        username: "Please enter login username",
        email: "Please enter your email",
        password: "Please enter your password",
        secondPassword: "Please enter your password",
        first_name: "First name is required",
        last_name: "Last name is required",
        affiliation: "The organization name is required",
        country: "Country is required",
        career_status: "Career status is required",
        groups: "Please select at least one group",
        default_category: "Default category is required",
        captcha_value: "Please fill",
        privacyPolicy: "no",
    });

    const [captchaUrl, setCaptchaUrl] = useState<string | undefined>();

    const [postSubmitDialog, setPostSubmitDialog] = useState<PostSubmitDialogProps>(
        {
            open: false,
            onClose: () => {
            },
            onConfirm: () => {
            },
            message: "",
            title: ""
        }
    );

    const fetchCaptchaToken = async () => {
        try {
            const getCaptchaToken = runtimeContext.aaaFetcher.path(ACCOUNT_REGISTER_URL).method('get').create();
            const response = await getCaptchaToken({});
            const data: TokenResponse = response.data;
            console.log("Setting captcha token", data.token);
            setFormData(prev => ({
                ...prev, token: data.token,
            }));
        } catch (error) {
            console.log("fetchCaptchaToken - " + error);
        }
    };

    useEffect(() => {
        console.log("" + JSON.stringify(formData));
        if (formData.token) {
            setCaptchaUrl(runtimeContext.AAA_URL + `/captcha/image?token=${formData.token}`);
        } else {
            fetchCaptchaToken();
        }
    }, [formData.token]);

    const resetCaptcha = useCallback(() => {
        fetchCaptchaToken();
    }, []);

    const speakCaptcha = () => {
        const audio = new Audio(runtimeContext.AAA_URL + `/captcha/audio?token=${formData.token}`);
        audio.play().catch((error) => console.error("Playback failed:", error));
    };

    const validateCaptcha = (value: string) => {
        return value.length > 4;
    };

    const validators: Record<string, (value: string) => void> = {
        "username": (value: string) => {
            const minUsernameLength = 3;
            if (value.length < minUsernameLength) {
                setErrors((prev) => ({
                    ...prev,
                    username: `User name must be minimum of ${minUsernameLength} characters`
                }));
            } else {
                setErrors((prev) => ({...prev, username: undefined}));
            }
        },
        "password": (value: string) => {
            if (!passwordValidator(value)) {
                setErrors((prev) => ({
                    ...prev,
                    password: `Password is invalid.`
                }));
            } else {
                setErrors((prev) => ({...prev, password: undefined}));
            }
        },
        "email": (value: string) => {
            if (!emailValidator(value)) {
                setErrors((prev) => ({
                    ...prev,
                    email: `Email is invalid`
                }));
            } else {
                setErrors((prev) => ({...prev, email: undefined}));
            }

        },
        "captcha_value": (value: string) => {
            if (!validateCaptcha(value)) {
                console.log("X captcha_value = " + value);
                setErrors((prev) => ({...prev, captcha_value: "Not provided"}));
            } else {
                console.log("O captcha_value = " + value);
                setErrors((prev) => ({...prev, captcha_value: undefined}));
            }
        },
        "first_name": (value: string) => {
            if (value) {
                setErrors((prev) => ({...prev, first_name: ""}));
            } else {
                setErrors((prev) => ({...prev, first_name: "First name is required"}));
            }
        },
        "last_name": (value: string) => {
            if (value) {
                setErrors((prev) => ({...prev, last_name: ""}));
            } else {
                setErrors((prev) => ({...prev, last_name: "Last name is required"}));
            }
        },
        "affiliation": (value: string) => {
            if (value && value.length > 1) {
                setErrors((prev) => ({...prev, affiliation: ""}));
            } else {
                setErrors((prev) => ({...prev, affiliation: "The organization name is required"}));
            }
        },
    }

    // Handle text field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
        // console.log("change: " + name + " = " + value)

        if (name === "secondPassword") {
            setSecondPassword(value);
            if (value !== formData.password) {
                setErrors((prev) => ({...prev, secondPassword: "Reentered password does not match"}));
            } else {
                setErrors((prev) => ({...prev, secondPassword: undefined}));
            }
        } else if (name === "privacyPolicy") {
            const {checked} = e.target;
            if (checked) {
                setErrors((prev) => ({...prev, privacyPolicy: undefined}));
            } else {
                setErrors((prev) => ({...prev, privacyPolicy: "no"}));
            }
        } else {
            setFormData(prev => ({
                ...prev,
                [name]: value,
            }));
        }

        const validator = validators[name];
        if (validator) {
            validator(value)
        }
    };

    useEffect(() => {
        // Check if errors object is empty and the form has been validated at least once

        const sendPreflightRequest = async () => {
            const hasNoErrors = Object.values(errors).every(value => value === "" || value === undefined);
            if (hasNoErrors) {
                try {
                    const preflightRequest = runtimeContext.aaaFetcher.path(ACCOUNT_REGISTER_PREFLIGHT_URL).method('post').create();
                    const response = await preflightRequest(formData);

                    if (response.ok) {
                        // Handle successful preflight
                        response.data.forEach((detail) => {
                            if (detail.field_name && detail.field_name in errors) {
                                setErrors(prev => ({
                                    ...prev,
                                    [detail.field_name as keyof typeof errors]: detail.message
                                }));
                            }

                            if (detail.field_name === "host") {
                                showNotification(detail.message, "error");
                            }

                            if (detail.field_name === "token") {
                                showNotification(detail.message, "error");
                            }

                        })
                    } else {
                        // Handle preflight validation errors
                        showNotification(JSON.stringify(response.data) as any, "error");
                    }
                } catch (error) {
                    console.error('Preflight request error:', error);
                    showNotification(JSON.stringify(error) as any, "error");
                }
            }
            else {
                console.log("Errors:", hasNoErrors, errors);
            }
        }

        sendPreflightRequest();

    }, [errors, formData]); // Dependencies for the effect


    // Handle form submission
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("Submit");
        event.preventDefault();

        if (!formData.captcha_value) {
            alert("Please complete the CAPTCHA before submitting.");
            return;
        }
        try {
            const postRegistration = runtimeContext.aaaFetcher.path(ACCOUNT_REGISTER_URL).method('post').create();
            const response = await postRegistration(formData);
            const data = response.data;
            console.log("Response:", data);

            if (response.ok) {
                setPostSubmitDialog({
                    open: true,
                    title: "Registration Success",
                    message: "Account is registered successfully! Please go to home page, and login.",
                    onConfirm: () => {
                        window.location.href = runtimeContext.POST_USER_REGISTRATION_URL;
                    },
                })
            } else {
                const errorReply: RegistrationErrorReply = data as unknown as RegistrationErrorReply;

                const messages = errorReply.map(an_error => an_error.field_name ? `${an_error.message} (error in ${an_error.field_name})` : an_error.message);
                showNotification(messages.join("\n"), "warning");

                if (response.status === 400) {
                    setPostSubmitDialog({
                        open: true,
                        title: "Registration Unsuccessful",
                        message: messages.join("\n"),
                        onClose: () => {
                            setPostSubmitDialog(
                                {
                                    ...postSubmitDialog,
                                    open: false,
                                }
                            )
                        },
                    });
                }
            }

        } catch (error) {
            console.error("Error:", error);
            setPostSubmitDialog({
                open: true,
                title: "Registration Unsuccessful",
                message: JSON.stringify(error),
                onClose: () => {
                    setPostSubmitDialog(
                        {
                            ...postSubmitDialog,
                            open: false,
                        }
                    )
                },
            });
        }
    };

    const hasErrors = Object.values(errors).some(value =>
        Array.isArray(value) ? value.length > 0 : value !== undefined && value !== null && value !== ''
    );
    const invalidFormData = hasErrors || !formData.username|| formData.username.length < 2 || formData.password !== secondPassword;

    return (
        <Container maxWidth="md" sx={{my: "4em"}} >
            <Box
                component="form"
                onSubmit={handleSubmit}
                sx={{display: "flex", flexDirection: "column", gap: "2em"}}
            >
                <Typography variant="h1" color="black" align="left" >
                    Create your arXiv account
                </Typography>

                <CardWithTitle title={"Account Credentials"}>
                    <Box sx={{p: 1, m: 1}}>
                        <Box sx={{display: "flex", gap: 1}}>
                            <TextField
                                label="Email (required)"
                                aria-label="Email address, required"
                                size="small"
                                error={Boolean(errors.email)}
                                helperText={errors.email}
                                name="email"
                                value={formData.email}
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 1}}
                            />
                            <FlexOne />
                        </Box>

                        <Box sx={{display: "flex", gap: 1, pt: 2}}>
                            <TextField
                                label="Username (required)"
                                aria-label="User name for login, required"
                                size="small"
                                error={Boolean(errors.username)}
                                helperText={errors.username}
                                name="username"
                                value={formData.username}
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 1}}
                            />
                            <FlexOne />

                        </Box>

                        <Box sx={{display: "flex", gap: 1,pt: 2}}>
                            <PasswordWrapper>
                                <TextField
                                    label="Password (required)"
                                    aria-label="Login password, required"
                                    size="small"
                                    error={Boolean(errors.password)}
                                    helperText={errors.password}
                                    name="password"
                                    value={formData.password}
                                    type="password"
                                    fullWidth
                                    onChange={handleChange}
                                />
                            </PasswordWrapper>

                            <PasswordWrapper>
                                <TextField
                                    label="Reenter password (required)"
                                    aria-label="Re-enter password for password verification"
                                    size="small"
                                    error={Boolean(errors.secondPassword)}
                                    helperText={errors.secondPassword}
                                    name="secondPassword"
                                    value={secondPassword}
                                    type="password"
                                    fullWidth
                                    onChange={handleChange}
                                />
                            </PasswordWrapper>
                        </Box>
                        <PasswordRequirements />

                    </Box>
                </CardWithTitle>

                <CardWithTitle title={"User Information"} >
                    <UserInfoForm formData={formData} setFormData={setFormData} errors={errors} setErrors={setErrors} />
                </CardWithTitle>

                <CardWithTitle title={"Submission Category"}>
                    <SubmissionCategoryForm formData={formData} setFormData={setFormData} setErrors={setErrors} />
                </CardWithTitle>

                <CardWithTitle title={"Verify and Submit"}>
                    <Box sx={{p: 1, m: 1}}>
                        <Typography>To prevent misuse let us know you are not a robot (required)</Typography>
                        <Box display="flex" justifyContent="space-between" alignItems="center" sx={{mt: 1, gap: 1}}>
                            <img key={captchaUrl} alt={"captcha"} src={captchaUrl}/>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography component="label"
                                    htmlFor="captcha_value"
                                    sx={{
                                        fontWeight: 'bold',
                                        flexShrink: 0,
                                    }}>
                                    Type captcha response:
                                </Typography>
                                <TextField
                                    aria-label="Captcha reply, required"
                                    size="small"
                                    id="captcha_value"
                                    name="captcha_value"
                                    value={formData.captcha_value}
                                    helperText={errors.captcha_value}
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{width: "13em"}}
                                />
                            </Box>
                            <FlexOne />
                        </Box>
                        <Button sx={{m: 1, fontSize: "10px"}} variant={"outlined"} onClick={resetCaptcha}
                                aria-label="Load new captcha"
                                startIcon={<RefreshIcon/>} title={"Load New Captcha"}>Load New Captcha</Button>
                        <Button sx={{m: 1, fontSize: "10px"}} variant={"outlined"} onClick={speakCaptcha}
                                aria-label="Listen to captcha value" startIcon={<HearingIcon/>}> Listen To
                            Audio</Button>
                        <LineDivider />

                        <Box sx={{display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap'}}>
                            <FormControlLabel
                                control={<Checkbox onChange={handleChange} name="privacyPolicy"/>}
                                label="I agree to the arXiv Privacy Policy."
                            />
                            <Link
                                sx={{
                                    border: 0,
                                    borderColor: "#aaa",
                                    borderRadius: '4px',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 0.5,
                                    padding: '4px 8px',
                                    whiteSpace: 'nowrap' // Prevent line break if you want it on one line
                                }}
                                href={runtimeContext.URLS.privacyPolicy}
                                target="_blank"
                            >
                                <LinkIcon sx={{fontSize: 18}}/>
                                Open Privacy Policy
                            </Link>
                        </Box>
                        <LineDivider />
                        <Typography>
                            You should only register with arXiv once. arXiv associates papers that you have
                            submitted with your user account. We must retain the information you submit for
                            registration indefinitely in order to preserve the scholarly record, support academic
                            integrity, and prevent abuse of our systems. If you register twice, with different
                            accounts, your submission history will be inaccurate.
                        </Typography>
                        <Box sx={{display: "flex", justifyContent: "space-between", m: 2}}>
                            <Box sx={{flex: 1}}/>
                            <Button type="submit" variant="contained" disabled={invalidFormData} sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": {
                                    backgroundColor: "#1420c0"
                                }
                            }}>
                                Submit to create your arXiv account
                            </Button>

                        </Box>

                    </Box>
                </CardWithTitle>
            </Box>

            <PostSubmitActionDialog {...postSubmitDialog} />
        </Container>
    );
};

export default AccountRegistration;
