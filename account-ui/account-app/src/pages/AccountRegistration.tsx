import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
// import Card from "@mui/material/Card";
import Container from "@mui/material/Container";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import Checkbox from "@mui/material/Checkbox";
import Link from "@mui/material/Link";
import Dialog from "@mui/material/Dialog";
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';

import React, {useCallback, useContext, useEffect, useState} from "react";
import CategoryGroupSelection, {CategoryGroupType} from "../bits/CategoryGroupSelection.tsx";
import CategoryChooser, {SelectedCategoryType} from "../bits/CategoryChooser.tsx";
import CountrySelector from "../bits/CountrySelector.tsx";
import CareerStatusSelect, {CareerStatusType} from "../bits/CareerStatus.tsx";
import {RuntimeContext} from "../RuntimeContext.tsx";
import {paths} from "../types/aaa-api.ts";
import RefreshIcon from "@mui/icons-material/Refresh";
import HearingIcon from "@mui/icons-material/Hearing";
import LinkIcon from "@mui/icons-material/Launch";
import {emailValidator, passwordValidator} from "../bits/validators.ts";
import Tooltip from "@mui/material/Tooltip";
import PasswordRequirements from "../bits/PasswordRequirements.tsx";
import {useNotification} from "../NotificationContext.tsx";
import {fetchPlus} from "../fetchPlus.ts";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import FormControlLabel from "@mui/material/FormControlLabel";

import {useMediaQuery, useTheme} from "@mui/material";
/* import IconButton from '@mui/material/IconButton';
import Collapse from '@mui/material/Collapse';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AccentedCharactersGuide from "../bits/AccentedChars.tsx";

 */

type TokenResponse = paths["/account/register/"]['get']['responses']['200']['content']['application/json'];
type SubmitRequest = paths["/account/register/"]['post']['requestBody']['content']['application/json'];
// type RegistrationSuccessReply = paths["/account/register/"]['post']['responses']['200']['content']['application/json'];
type RegistrationErrorReply = paths["/account/register/"]['post']['responses']['400']['content']['application/json'];

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

const AccountRegistration = () => {
    const runtimeContext = useContext(RuntimeContext);
    const {showNotification} = useNotification();
    const theme = useTheme();
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

    const [errors, setErrors] = useState<{
        username?: string,
        email?: string,
        password?: string,
        secondPassword?: string,
        first_name?: string,
        last_name?: string,
        suffix_name?: string,
        affiliation?: string,
        country?: string,
        career_status?: string,
        groups?: string,
        default_category?: string,
        captcha_value?: string,
        privacyPolicy?: string,
    }>({groups: "Please select at least one group", captcha_value: "Please fill", privacyPolicy: "no"});

    const [captchaUrl, setCaptchaUrl] = useState<string | undefined>();

    const setSelectedGroups = (groups: CategoryGroupType[]) => {
        setFormData(prev => ({...prev, groups: groups}));
        if (groups.length > 0) {
            setErrors(prev => ({...prev, groups: ""}));
        } else {
            setErrors(prev => ({...prev, groups: "Please select at least one group"}));
        }
    }

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
            const response = await fetchPlus(runtimeContext.AAA_URL + "/account/register/");
            const data: TokenResponse = await response.json();
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
        }
    }

    // Handle text field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
        console.log("change: " + name + " = " + value)

        if (name === "secondPassword") {
            setSecondPassword(value);
            if (value !== formData.password) {
                setErrors((prev) => ({...prev, secondPassword: "Reentered password does not match"}));
            } else {
                setErrors((prev) => ({...prev, secondPassword: undefined}));
            }
        }
        else if (name === "privacyPolicy") {
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

    const setCarrerStatus = (value: CareerStatusType | null) => {
        if (value) {
            setFormData(prev => ({...prev, career_status: value}));
        }
    };

    const setCountry = (value: string | null) => {
        if (value) {
            setFormData(prev => ({...prev, country: value}));
        }
    };

    const setDefaultCategory = (cat: SelectedCategoryType | null) => {
        if (cat) {
            setFormData(prev => ({
                ...prev,
                default_category: {archive: cat.archive, subject_class: cat.subject_class || "*"}
            }));
        }
    }

    // Handle form submission
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        console.log("Submit");
        event.preventDefault();

        if (!formData.captcha_value) {
            alert("Please complete the CAPTCHA before submitting.");
            return;
        }
        try {
            const response = await fetchPlus(runtimeContext.AAA_URL + "/account/register/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });
            const data = await response.json();
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
                const message = errorReply.field_name ? `${errorReply.message} (error in ${errorReply.field_name})` : errorReply.message;
                showNotification(message, "warning");

                if (response.status === 400) {
                    setPostSubmitDialog({
                        open: true,
                        title: "Registration Unsuccessful",
                        message: message,
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
    const invalidFormData = hasErrors || formData.username.length < 2 || formData.password.length < 10 || formData.password !== secondPassword;

    const isSmallScreen = useMediaQuery(theme.breakpoints.down("sm")); // 'sm' is ~600px

    return (
        <Container maxWidth="md" sx={{mt: 2}}>
            <Box
                component="form"
                onSubmit={handleSubmit}
                sx={{display: "flex", flexDirection: "column", gap: 1}}
            >
                <Typography variant="h4" color="black"  align="left" sx={{fontWeight: "bold"}}>
                    Create your arXiv account
                </Typography>
                <Box sx={{mx:2}}>

                </Box>
                {/* Registration Form */}
                <CardWithTitle title={"Account Credentials"}>
                    <Box sx={{p:1, m: 1}}>
                        <Typography variant="subtitle2" color="black" align="left">
                            It is a violation of our policies to misrepresent your identity or
                            institutional affiliation. Claimed affiliation should be current in the
                            conventional sense: e.g., physical presence, funding, e-mail address,
                            mention on institutional web pages, etc. Misrepresentation of identity or
                            affiliation, for any reason, is possible grounds for immediate and
                            permanent suspension.
                        </Typography>
                        <Box sx={{ display: "flex", gap: 1 }}>
                            <Box sx={{ flex: 1 }}>
                                <Typography fontWeight="bold" sx={{ mb: 1 }}>{"Email (required): "}</Typography>
                                <TextField
                                    size="small"
                                    error={Boolean(errors.email)}
                                    helperText={errors.email}
                                    name="email"
                                    value={formData.email}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                />
                            </Box>

                            <Box sx={{ flex: 1 }}>
                                <Typography fontWeight="bold" sx={{ mb: 1 }}>{"Username (required): "}</Typography>
                                <TextField
                                    size="small"
                                    error={Boolean(errors.username)}
                                    helperText={errors.username}
                                    name="username"
                                    value={formData.username}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                />
                            </Box>
                        </Box>

                        <Box sx={{ display: "flex", gap: 1 }}>
                            <Box sx={{ flex: 1, pt: 2 }}>

                                <Typography fontWeight={"bold"}
                                        sx={{mb: 1}}>{"Password (required)"}</Typography>
                                <Tooltip title={<PasswordRequirements/>}>
                                    <TextField
                                        size="small"
                                        error={Boolean(errors.password)}
                                        helperText={errors.password}
                                        name="password"
                                        value={formData.password}
                                        type="password"
                                        variant="outlined"
                                        fullWidth
                                        onChange={handleChange}
                                        sx={{flex: 1}} // Ensures both fields take equal width
                                    />
                                </Tooltip>
                            </Box>
                            <Box sx={{ flex: 1, pt: 2 }}>

                                <Typography fontWeight={"bold"}
                                            sx={{mb: 1}}>{"Reenter password (required):  "}</Typography>

                                <TextField
                                    size="small"
                                    error={Boolean(errors.secondPassword)}
                                    helperText={errors.secondPassword}
                                    name="secondPassword"
                                    value={secondPassword}
                                    type="password"
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 1}} // Ensures both fields take equal width
                                />
                            </Box>
                        </Box>
                    </Box>
                </CardWithTitle>

                <CardWithTitle title={"User Information"}>
                    <Box sx={{p:1, m: 1}}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                        <Typography sx={{mt:0}} variant={"body2"}>Names accept pidgin TeX (\'o) for foreign characters</Typography>
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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                            <Link
                                sx={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 0.5,
                                    padding: '4px 8px',
                                    whiteSpace: 'nowrap' // Prevent line break if you want it on one line
                                }}
                                href={runtimeContext.URLS.accentedCharactersGuide}
                                target='_blank'
                            >
                                <LinkIcon sx={{ fontSize: 18 }} />
                                Open Accented Characters Guide
                            </Link>
                        </Box>
                        </Box>


                        <Box sx={{ display: "flex", gap: 1 }}>
                            <Box sx={{ flex: 2 }}>
                                <Box sx={{ flex: 1, pt: 2 }}>
                                    <Typography fontWeight={"bold"} sx={{mb: 1}}>{"First name (required)"}</Typography>
                                <TextField
                                    size="small"
                                    error={Boolean(errors.first_name)}
                                    helperText={errors.first_name}
                                    name="first_name"
                                    value={formData.first_name}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 3}} // Ensures both fields take equal width
                                />
                                </Box>
                            </Box>
                            <Box sx={{ flex: 2 }}>
                                <Box sx={{ flex: 1, pt: 2 }}>
                                    <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Sur name / Last name / Family name (required)"}</Typography>

                                    <TextField
                                    size="small"
                                    error={Boolean(errors.last_name)}
                                    helperText={errors.last_name}
                                    name="last_name"
                                    value={formData.last_name}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 3}} // Ensures both fields take equal width
                                />
                                </Box> </Box>
                            <Box sx={{ flex: 2 }}>
                                <Box sx={{ flex: 1, pt: 2 }}>
                                    <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Suffix: "}
                                        <Typography variant={"caption"}>
                                            {"examples: Jr. , Sr. , Ph.D, etc."}
                                        </Typography>
                                    </Typography>

                                <TextField
                                    size="small"
                                    error={Boolean(errors.suffix_name)}
                                    helperText={errors.suffix_name}
                                    name="suffix_name"
                                    value={formData.suffix_name}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 1}} // Ensures both fields take equal width
                                />
                                </Box>
                            </Box>
                        </Box>

                        <Box sx={{ display: "flex", gap: 1 }}>
                            <Box sx={{ flex: 2 }}>
                                <Typography fontWeight={"bold"} sx={{mb: 1, pt: 2}}>{"Country (required)"}</Typography>
                                <CountrySelector onSelect={setCountry} selectedCountry={formData.country || ""}/>
                            </Box>
                            <Box sx={{ flex: 2 }}>
                                <Typography fontWeight={"bold"} sx={{mb: 1, pt: 2}}>{"Organization name (required)"}</Typography>
                                <TextField
                                    size="small"
                                    error={Boolean(errors.affiliation)}
                                    helperText={errors.affiliation}
                                    name="affiliation"
                                    value={formData.affiliation}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 3}} // Ensures both fields take equal width
                                />
                            </Box>

                            <Box sx={{ flex: 2 }}>
                                <Typography fontWeight={"bold"}
                                            sx={{mb: 1, pt: 2}}>{"Career Stage (required)"}</Typography>
                                <CareerStatusSelect onSelect={setCarrerStatus} careereStatus={formData.career_status}/>
                            </Box>
                        </Box>

                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1, pt: 2}}>{"Home page URL"}</Typography>
                            <TextField
                                size="small"
                                name="url"
                                value={formData.url}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 1}}
                            />
                        </Box>

                    </Box>
                </CardWithTitle>
                <CardWithTitle title={"Submission Category"}>
                    <Box sx={{p:1, m: 1}}>

                        <CategoryGroupSelection selectedGroups={formData.groups as unknown as CategoryGroupType[]}
                                                setSelectedGroups={setSelectedGroups}
                                                isSmallScreen={isSmallScreen}
                        />
                        <Box sx={{pb: 1}}>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Your default category (required)"}</Typography>
                            <CategoryChooser onSelect={setDefaultCategory}
                                             selectedCategory={formData.default_category}/>
                        </Box>
                    </Box>
                </CardWithTitle>
                <CardWithTitle title={"Verify and Submit"}>
                    <Box sx={{p:1, m: 1}}>
                        <Typography>To prevent misuse, let us know you are not a robot (required)</Typography>
                        <Box>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                                <img key={captchaUrl} alt={"captcha"} src={captchaUrl}/>

                                <TextField
                                    size="small"
                                    name="captcha_value"
                                    value={formData.captcha_value}
                                    variant="outlined"
                                    helperText={errors.captcha_value}
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{width: "13em", ml: 2}}
                                />
                                <Box sx={{flex: 1}}/>

                            </Box>

                        </Box>
                        <Box>
                            <Button sx={{m: 1, fontSize: "10px"}} variant={"outlined"} onClick={resetCaptcha} startIcon={<RefreshIcon/>} title={"Load New Captcha"}>Load New Captcha</Button>
                            <Button sx={{m: 1, fontSize: "10px"}} variant={"outlined"} onClick={speakCaptcha} aria-label="Listen to captcha value" startIcon={<HearingIcon/>}> Listen To Audio</Button>
                        </Box>
                        <Box sx={{border: 1, my: 1}}></Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                            <FormControlLabel
                                control={<Checkbox onChange={handleChange} name="privacyPolicy" />}
                                label="I agree to the arXiv Privacy Policy."
                            />
                            <Link
                                sx={{
                                    border: 2,
                                    borderColor: "#aaa",
                                    borderRadius: '4px',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 0.5,
                                    padding: '4px 8px',
                                    whiteSpace: 'nowrap' // Prevent line break if you want it on one line
                                }}
                                href={runtimeContext.URLS.privacyPolicy}
                            >
                                <LinkIcon sx={{ fontSize: 18 }} />
                                Open Privacy Policy
                            </Link>
                        </Box>
                        <Box sx={{border: 1, my: 1}}></Box>
                        <Box>
                            <Typography>
                                You should only register with arXiv once. arXiv associates papers that you have submitted with your user account. We must retain the information you submit for registration indefinitely in order to preserve the scholarly record, support academic integrity, and prevent abuse of our systems. If you register twice, with different accounts, your submission history will be inaccurate.
                            </Typography>
                        </Box>
                        <Box sx={{display: "flex", justifyContent: "space-between", m: 2}}>
                            <Box sx={{flex: 1}} />
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
