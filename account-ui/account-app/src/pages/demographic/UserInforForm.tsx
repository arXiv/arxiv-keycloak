import React, {useContext} from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";

import CountrySelector from "../../bits/CountrySelector.tsx";
import CareerStatusSelect, {CareerStatusType} from "../../bits/CareerStatus.tsx";
import {paths} from "../../types/aaa-api.ts";
import LinkIcon from "@mui/icons-material/Launch";

// import {useTheme} from "@mui/material";
import TextField from "@mui/material/TextField";
import LineDivider from "../../bits/LineDevider.tsx";
import {RuntimeContext} from "../../RuntimeContext.tsx";
import {AccountFormError} from "./AccountFormError.ts";

// type TokenResponse = paths["/account/register/"]['get']['responses']['200']['content']['application/json'];
type SubmitRequest = paths["/account/register/"]['post']['requestBody']['content']['application/json'];
type UpdateProfileRequest = paths["/account/profile/"]['put']['requestBody']['content']['application/json'];

// type RegistrationSuccessReply = paths["/account/register/"]['post']['responses']['200']['content']['application/json'];
// type RegistrationErrorReply = paths["/account/register/"]['post']['responses']['400']['content']['application/json'];

const FlexOne = () => <Box sx={{flex: 1}} />


const UserInfoForm = <T extends SubmitRequest | UpdateProfileRequest>(
    { formData, setFormData, errors, setErrors
    }: {
    formData: T;
    setFormData: React.Dispatch<React.SetStateAction<T>>;
    errors: AccountFormError,
    setErrors: React.Dispatch<React.SetStateAction<AccountFormError>>;
}) => {
    const runtimeContext = useContext(RuntimeContext);


    // Handle text field changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;

        setFormData(prev => ({
            ...prev,
            [name]: value,
        }));

        const validator = validators[name];
        if (validator) {
            validator(value)
        }
    };

    const validators: Record<string, (value: string) => void> = {
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

    const setCareerStatus = (value: CareerStatusType | null) => {
        console.log("setCareerStatus: " + JSON.stringify(value));

        if (value && value !== "Unknown") {
            setFormData(prev => ({...prev, career_status: value}));
            setErrors((prev) => ({...prev, career_status: ""}));
        } else {
            setFormData(prev => ({...prev, career_status: "Unknown"}));
            setErrors((prev) => ({...prev, career_status: "Career status is required"}));
        }
    };

    const setCountry = (value: string | null) => {
        console.log("setCountry: " + JSON.stringify(value));

        if (value) {
            setErrors((prev) => ({...prev, country: ""}));
            setFormData(prev => ({...prev, country: value}));
        } else {
            setErrors((prev) => ({...prev, country: "Country is required"}));
            setFormData(prev => ({...prev, country: ""}));
        }
    };


    return (
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
                <TextField
                    label="First name (required)"
                    aria-label="First name or given name, required"
                    size="small"
                    error={Boolean(errors.first_name)}
                    helperText={errors.first_name}
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    sx={{flex: 1}}
                />
                <FlexOne />
            </Box>

            <Box sx={{display: "flex", gap: 1, pt: 2}}>
                <TextField
                    label="Sur name / Last name / Family name (required)"
                    aria-label="Sur name, Last name, Family name, required"
                    size="small"
                    error={Boolean(errors.last_name)}
                    helperText={errors.last_name}
                    name="last_name"
                    value={formData.last_name}
                    sx={{flex: 1}}
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
                    <TextField
                        id="suffix_name"
                        aria-label="Suffix,examples include Jr. Sr, II, etc. Do not input honorifics like Esequire or Ph.D."
                        size="small"
                        error={Boolean(errors.suffix_name)}
                        helperText={errors.suffix_name}
                        name="suffix_name"
                        value={formData.suffix_name}
                        sx={{flex: 1}}
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
                    <CareerStatusSelect onSelect={setCareerStatus} careereStatus={formData.career_status}/>
                </Box>
            </Box>
            <Box sx={{display: "flex", pt: 2}}>
                <TextField
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
                <TextField
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

    );
}

export default UserInfoForm;
