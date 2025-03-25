import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
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
import {emailValidator, passwordValidator} from "../bits/validators.ts";
import Tooltip from "@mui/material/Tooltip";
import PasswordRequirements from "../bits/PasswordRequirements.tsx";
import {useNotification} from "../NotificationContext.tsx";
import {fetchPlus} from "../fetchPlus.ts";

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
        captcha_value?: string
    }>({groups: "Please select at least one group", captcha_value: "Please fill"});

    const [captchaImage, setCaptchaImage] = useState<React.ReactNode | null>(null);

    const setSelectedGroups = (groups: CategoryGroupType[]) => {
        setFormData({...formData, groups: groups});
        if (groups.length > 0) {
            setErrors({...errors, groups: ""});
        } else {
            setErrors({...errors, groups: "Please select at least one group"});
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


    useEffect(() => {
        console.log(JSON.stringify(formData));
        if (formData.token) {
            setCaptchaImage(
                <img alt={"captcha"} src={runtimeContext.AAA_URL + `/captcha/image?token=${formData.token}`}/>
            )
        } else {
            fetchPlus(runtimeContext.AAA_URL + "/account/register/")
                .then(response => response.json()
                    .then((data: TokenResponse) => setFormData(
                        {
                            ...formData, token: data.token,
                        }
                    )));
        }
    }, [formData.token]);

    const resetCaptcha = useCallback(() => {
        setFormData({...formData, token: ""});
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
        } else {
            setFormData({
                ...formData,
                [name]: value,
            });
        }

        const validator = validators[name];
        if (validator) {
            validator(value)
        }
    };

    const setCarrerStatus = (value: CareerStatusType | null) => {
        if (value) {
            setFormData({...formData, career_status: value})
        }
    };

    const setCountry = (value: string | null) => {
        if (value) {
            setFormData({...formData, country: value})
        }
    };

    const setDefaultCategory = (cat: SelectedCategoryType | null) => {
        if (cat) {
            setFormData({
                ...formData,
                default_category: {archive: cat.archive, subject_class: cat.subject_class || "*"}
            });
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

    return (
        <Container maxWidth="md" sx={{mt: 2}}>
            <Typography variant={"h5"}>Register for the first time</Typography>
            {/* Privacy Policy Notice */}
            <Card elevation={3} sx={{px: 3, py: 2, mb: 2, backgroundColor: "#eeeef8"}}>
                <Typography variant="body1" fontWeight={"bold"} color="textPrimary" align="left">
                    {"By registering with arXiv you are agreeing to the "}
                    <Link href={runtimeContext.URLS.privacyPolicy} target="_blank" rel="noopener" underline="hover">
                        arXiv Privacy Policy
                    </Link>
                    {"."}
                </Typography>
            </Card>

            {/* Register once */}
            <Card elevation={3} sx={{px: 3, py: 1, mb: 2, backgroundColor: "#F8F8F8"}}>
                <Typography variant="body1" color="black" align="left">
                    <Typography fontWeight={"bold"}
                                component="span">{"You should only register with arXiv once: "}</Typography>
                    arXiv associates papers that you have submitted with your user account. We must retain the
                    information you submit for registration indefinitely in order to preserve the scholarly record,
                    support academic integrity, and prevent abuse of our systems. If you register twice, with different
                    accounts, your submission history will be inaccurate.
                </Typography>
            </Card>

            {/* Registration Form */}
            <Card elevation={0}
                  sx={{
                      p: 1,
                      position: 'relative',
                      paddingTop: '48px', // Add padding to push content down
                      marginTop: '24px', // Add margin to shift the entire card (including shadow)

                      '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: '16px', // Push the border down by 24px
                          left: 0,
                          right: 0,
                          height: '95%',
                          backgroundColor: 'transparent',
                          border: '2px solid #ddd', // Add the border
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
                        Account registration
                    </Typography>
                </Box>

                <CardContent sx={{py: 0}}>
                    <Box
                        component="form"
                        onSubmit={handleSubmit}
                        sx={{display: "flex", flexDirection: "column", gap: 1}}
                    >
                        <Typography variant={"body2"} fontWeight={"bold"}>
                            Fields with * are required.
                        </Typography>

                        <Box>
                            <Typography fontWeight={"bold"}>{"Email: "}</Typography>
                            <Typography sx={{paddingLeft: 3, mb: 1}}>{"You "}
                                <Typography component="span" fontWeight="bold">{"must"}</Typography>
                                {" able to receive mail at this address to register. We take "}
                                <Link href={runtimeContext.URLS.emailProtection} target="_blank" rel="noopener"
                                      underline="hover">strong measure</Link>
                                {" to protect your email address from viruses and spam. Do not register with an e-mail address that belongs to someone else: if we discover that you've done so, we will suspend your account."}
                            </Typography>
                            <TextField label="Email *" sx={{flex: 2}}
                                       error={Boolean(errors.email)}
                                       helperText={errors.email}
                                       name="email" value={formData.email} variant="outlined" fullWidth
                                       onChange={handleChange}/>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"User name: "}</Typography>
                            <Box sx={{display: "flex", gap: 2}}>
                                <TextField label="Username *" sx={{flex: 1}}
                                           error={Boolean(errors.username)}
                                           helperText={errors.username}
                                           name="username" value={formData.username} variant="outlined" fullWidth
                                           onChange={handleChange}/>
                            </Box>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"}
                                        sx={{mb: 1}}>{"Password and reenter password:  "}</Typography>
                            <Box sx={{display: "flex", gap: 2}}>
                                <Tooltip title={<PasswordRequirements />} >
                                <TextField
                                    label="Password *"
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

                                <TextField
                                    label="Reenter Password *"
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
                        <Box sx={{display: "flex", gap: 2}}>
                            <Typography variant={"body2"}>
                                Please supply your correct name and affiliation.
                                It is a violation of our policies to misrepresent your identity or institutional
                                affiliation. Claimed affiliation should be current in the conventional sense: e.g.,
                                physical presence, funding, e-mail address, mention on institutional web pages, etc.
                                Misrepresentation of identity or affiliation, for any reason, is possible grounds for
                                immediate and permanent suspension.
                                <Typography variant={"inherit"} sx={{fontWeight: "bold"}}>
                                    Names and Organization fields accept pidgin TeX (\'o) for foreign characters.
                                </Typography>
                            </Typography>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"First, Last and Sur name:  "}</Typography>
                            <Box sx={{display: "flex", gap: 2}}>
                                <TextField
                                    label="First name *"
                                    error={Boolean(errors.first_name)}
                                    helperText={errors.first_name}
                                    name="first_name"
                                    value={formData.first_name}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 3}} // Ensures both fields take equal width
                                />
                                <TextField
                                    label="Last name *"
                                    error={Boolean(errors.last_name)}
                                    helperText={errors.last_name}
                                    name="last_name"
                                    value={formData.last_name}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 3}} // Ensures both fields take equal width
                                />
                                <TextField
                                    label="Sur name"
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

                        <Box>
                            <Typography fontWeight={"bold"}
                                        sx={{mb: 1}}>{"Organization, Country and Career Status:  "}</Typography>
                            <Box sx={{display: "flex", gap: 2}}>
                                <TextField
                                    label="Organization *"
                                    error={Boolean(errors.affiliation)}
                                    helperText={errors.affiliation}
                                    name="affiliation"
                                    value={formData.affiliation}
                                    variant="outlined"
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{flex: 3}} // Ensures both fields take equal width
                                />
                                <CountrySelector onSelect={setCountry} selectedCountry={formData.country || ""}/>
                                <CareerStatusSelect onSelect={setCarrerStatus} careereStatus={formData.career_status}/>
                            </Box>
                        </Box>
                        <CategoryGroupSelection selectedGroups={formData.groups as unknown as CategoryGroupType[]}
                                                setSelectedGroups={setSelectedGroups}/>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Your default category:  "}</Typography>
                            <CategoryChooser onSelect={setDefaultCategory} selectedCategory={formData.default_category}/>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Home page URL:  "}</Typography>
                            <TextField
                                label="Your Homepage URL"
                                name="url"
                                value={formData.url}
                                variant="outlined"
                                fullWidth
                                onChange={handleChange}
                                sx={{flex: 1}}
                            />
                        </Box>

                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Verification:  "}</Typography>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                                {captchaImage}
                                <IconButton onClick={resetCaptcha}> <RefreshIcon/></IconButton>
                                <IconButton onClick={speakCaptcha} aria-label="Listen to captcha value"> <HearingIcon/></IconButton>

                                <TextField
                                    label="Captcha Respones *"
                                    name="captcha_value"
                                    value={formData.captcha_value}
                                    variant="outlined"
                                    helperText={errors.captcha_value}
                                    fullWidth
                                    onChange={handleChange}
                                    sx={{width: "12em"}}
                                />
                                <Box sx={{flex: 1}}/>

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
                    </Box>
                </CardContent>
            </Card>

            <PostSubmitActionDialog {...postSubmitDialog} />
        </Container>
    );
};

export default AccountRegistration;
