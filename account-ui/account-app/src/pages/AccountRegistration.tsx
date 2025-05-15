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
import {useNotification} from "../NotificationContext.tsx";
import {fetchPlus} from "../fetchPlus.ts";
import CardWithTitle from "../bits/CardWithTitle.tsx";
import FormControlLabel from "@mui/material/FormControlLabel";

// import {useTheme} from "@mui/material";
import TextField from "@mui/material/TextField";
import PlainTextField from "../bits/PlainTextFiled.tsx";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import {Divider, ListItemText} from "@mui/material";
import PasswordWrapper from "../bits/PasswordWrapper.tsx";
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

const LineDivider = () => <Divider sx={{borderColor: '#666', my: 2, borderBottomWidth: '2px'}} />;
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

    const passwordRequirements = [
        "8 characters or more in length",
        "May contain uppercase letters, lowercase letters, numbers and special characters",
        "Must contain at least one special character"
    ];

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
                            <PlainTextField
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
                            <PlainTextField
                                label="Uesrname (required)"
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
                                <PlainTextField
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
                                <PlainTextField
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
                        <Typography sx={{mt: 2}}>
                            Password requirements
                                <List component="ol" sx={{ listStyleType: 'decimal', pl: 3, py: 0 }}>
                                    {
                                        passwordRequirements.map((paragraph) => (
                                            <ListItem component="li" sx={{ display: 'list-item', pl: 0, py: 0 }} >
                                                <ListItemText>
                                                    {paragraph}
                                                </ListItemText>
                                            </ListItem>
                                        ))
                                    }
                                </List>
                        </Typography>

                    </Box>
                </CardWithTitle>

                <CardWithTitle title={"User Information"} >
                    <Box sx={{p: 1, gap: 1}}>
                        <Typography variant="body1" fontWeight="bold" color="black" align="left" sx={{mx: 3}}>
                            It is a violation of our policies to misrepresent your identity or
                            institutional affiliation. Claimed affiliation should be current in the
                            conventional sense: e.g., physical presence, funding, e-mail address,
                            mention on institutional web pages, etc. Misrepresentation of identity or
                            affiliation, for any reason, is possible grounds for immediate and
                            permanent suspension.
                        </Typography>
                        <LineDivider />
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
                                    href={runtimeContext.URLS.accentedCharactersGuide}
                                    target='_blank'
                                >
                                    <LinkIcon sx={{fontSize: 18}}/>
                                    Open Accented Characters Guide
                                </Link>
                            </Box>
                        </Box>

                        <Box sx={{display: "flex", gap: 1, pt: 2}}>
                            <PlainTextField
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
                            <FlexOne />
                        </Box>

                        <Box sx={{display: "flex", gap: 1, pt: 2}}>
                            <PlainTextField
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
                            <FlexOne />
                        </Box>
                        <Box sx={{display: "flex", gap: 1, pt: 2}}>
                            <Box sx={{flex: 1}}>
                                <Typography component="label" fontWeight="bold" htmlFor="suffix_name">
                                    Suffix:
                                </Typography>
                                <Typography variant="body2" color="text.Secondary" sx={{ml: 1, mb: 0.5 }}>
                                    Examples include Jr. Sr, II, etc. Do not input honorifics like Esquire or Ph.D.
                                </Typography>
                                <PlainTextField
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
                        <LineDivider />
                        <Box sx={{display: "flex", gap: 1}}>
                            <Box sx={{flex: 1}}>
                                <CountrySelector onSelect={setCountry} selectedCountry={formData.country || ""}/>
                            </Box>
                            <Box sx={{flex: 1}}>
                                <CareerStatusSelect onSelect={setCarrerStatus} careereStatus={formData.career_status}/>
                            </Box>
                        </Box>
                        <Box sx={{display: "flex", pt: 2}}>
                            <PlainTextField
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
                            <PlainTextField
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
                </CardWithTitle>

                <CardWithTitle title={"Submission Category"}>
                    <Box sx={{p: 1, m: 1}}>
                        <CategoryGroupSelection selectedGroups={formData.groups as unknown as CategoryGroupType[]}
                                                setSelectedGroups={setSelectedGroups}
                        />
                        <Box sx={{pb: 1, mt: 2}}>
                            <CategoryChooser onSelect={setDefaultCategory}
                                             selectedCategory={formData.default_category}/>
                        </Box>
                    </Box>
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
