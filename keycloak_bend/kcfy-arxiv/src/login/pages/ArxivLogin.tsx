import React, { useState } from "react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import { clsx } from "keycloakify/tools/clsx";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import Link from "@mui/material/Link";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import CardActions from "@mui/material/CardActions";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import PasswordWrapper from "../PasswordWrapper.tsx";

// import  CardHeader from "@mui/material/CardHeader";
import ProviderIcon from "@mui/icons-material/InputRounded";
import GoogleIcon from "@mui/icons-material/Google";
import MicrosoftIcon from "@mui/icons-material/Microsoft";
import FacebookIcon from "@mui/icons-material/Facebook";
import TwitterIcon from "@mui/icons-material/Twitter";
import InstagramIcon from "@mui/icons-material/Instagram";
import GitHubIcon from "@mui/icons-material/GitHub";
import SSOIcon from "@mui/icons-material/CloudDone"

export default function ArxivLogin(props: PageProps<Extract<KcContext, { pageId: "login.ftl" }>, I18n>) {
    const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

    const registrationUrl = kcContext.properties.ARXIV_USER_REGISTRATION_URL;

    const { kcClsx } = getKcClsx({
        doUseDefaultCss,
        classes
    });

    const { social, realm, url, usernameHidden, login, auth, registrationDisabled, messagesPerField } = kcContext;

    const { msg, msgStr } = i18n;

    const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

    const userNameHasError = messagesPerField.existsError("username", "password");
    const userNameLabelText = !realm.loginWithEmailAllowed
        ? msg("username")
        : !realm.registrationEmailAsUsername
          ? msg("usernameOrEmail")
          : msg("email");

    // Check if there's an error for the username field
    const errorHtml = userNameHasError ? kcSanitize(messagesPerField.getFirstError("username", "password")) : "";

    const newUserComponent = (
        <Box  sx={{ p: 3, mt: 2 }}>
            <Typography variant="h2" gutterBottom>
                {"If you've never logged in to arXiv.org"}
            </Typography>
            <Box>
                <Button
                    tabIndex={8}
                    variant="contained"
                    color="primary"
                    href={registrationUrl}
                >
                    {"Register for the first time"}
                </Button>
                <Typography variant="h6" component="div" maxWidth={"30rem"}>
                    Registration is required to submit or update papers, but is not necessary to view them.
                </Typography>
            </Box>
        </Box>
    );

    const newUserPanel = (
        <Container maxWidth="sm">
            {newUserComponent}
        </Container>
    );

    function specificProviderIcon(providerId: string) {
        const specificProviderIcons = {
            "google": <GoogleIcon />,
            "facebook": <FacebookIcon />,
            "microsoft": <MicrosoftIcon />,
            "github": <GitHubIcon />,
            "twitter": <TwitterIcon />,
            "instagram": <InstagramIcon />,
            "sso": <SSOIcon />,
        };
        if (providerId in specificProviderIcons) {
            return specificProviderIcons[providerId as unknown as keyof typeof specificProviderIcons];
        }
        return (<ProviderIcon />);
    }

    return (
        <>
            <Template
                kcContext={kcContext}
                i18n={i18n}
                doUseDefaultCss={doUseDefaultCss}
                classes={classes}
                displayMessage={!messagesPerField.existsError("username", "password")}
                headerNode={null}
                displayInfo={realm.password && realm.registrationAllowed && !registrationDisabled}
                infoNode={newUserPanel}
                socialProvidersNode={
                    <>
                        {realm.password && social?.providers && social?.providers?.length > 0 && (
                            <Box id="kc-social-providers" mt={3}>
                                <Typography variant="h1">{msg("identity-provider-login-label")}</Typography>
                                <Box
                                    component="ul"
                                    sx={{
                                        listStyle: "none",
                                        padding: 0,
                                        display: "flex",
                                        flexWrap: "wrap",
                                        gap: 2,
                                        ...(social.providers.length > 3 && { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))" }),
                                    }}
                                >
                                    {social.providers.map((...[p, , providers]) => (
                                        <Box component="li" key={p.alias}>
                                            <Button
                                                id={`social-${p.alias}`}
                                                variant="text"
                                                href={p.loginUrl}
                                                startIcon={specificProviderIcon(p.providerId)}
                                                sx={{
                                                    textTransform: "none",
                                                    width: "100%",
                                                    display: "flex",
                                                    justifyContent: "center",
                                                    alignItems: "center",
                                                    gap: 1,
                                                    ...(providers.length > 3 && { display: "grid" }),
                                                }}
                                            >
                                                <Box
                                                    component="span"
                                                    className={clsx(kcClsx("kcFormSocialAccountNameClass"), p.iconClasses && "kc-social-icon-text")}
                                                    dangerouslySetInnerHTML={{ __html: kcSanitize(p.displayName) }}
                                                />
                                            </Button>
                                        </Box>
                                    ))}
                                </Box>
                            </Box>
                        )}

                    </>
                }
            >
                <Container id="kc-form" maxWidth="sm" sx={{ mt: 2 }}>
                    <Typography variant={"h1"} sx={{ p: 2 }}>
                        Login to arXiv.org{" "}
                    </Typography>

                    {/* Privacy Policy Notice */}
                    <Card elevation={3} sx={{ p: 3, mb: 3, backgroundColor: "#eeeef8" }}>
                        <Typography variant="body1" fontWeight={"bold"} color="textSecondary" align="left">
                            {"The "}
                            <Link href={registrationUrl} target="_blank" rel="noopener" underline="hover">
                                arXiv Privacy Policy
                            </Link>
                            {" has changed. By continuing to use arxiv.org, you are agreeing to the privacy policy."}
                        </Typography>
                    </Card>

                    <Card
                        elevation={0}
                        sx={{
                            p: 3,
                            position: "relative",
                            paddingTop: "48px", // Add padding to push content down
                            marginTop: "24px", // Add margin to shift the entire card (including shadow)

                            "&::before": {
                                content: '""',
                                position: "absolute",
                                top: "16px", // Push the border down by 24px
                                left: 0,
                                right: 0,
                                height: "90%",
                                backgroundColor: "transparent",
                                borderTop: "2px solid #ddd", // Add the border
                                borderLeft: "2px solid #ddd", // Add the border
                                borderRight: "2px solid #ddd", // Add the border
                                borderBottom: "2px solid #ddd" // Add the border
                            }
                        }}
                    >
                        <Box
                            sx={{
                                display: "flex",
                                justifyContent: "left",
                                alignItems: "left",
                                width: "100%",
                                position: "relative",
                                marginTop: "-44px", // Adjust this to move the title up
                                marginBottom: "16px"
                            }}
                        >
                            <Typography
                                variant="h2"
                                sx={{
                                    backgroundColor: "white",
                                    px: 2,
                                    zIndex: 1 // Ensure the text is above the border
                                }}
                            >
                                {"If you're already registered"}
                            </Typography>
                        </Box>

                        <div id="kc-form-wrapper">
                            {realm.password && (
                                <form
                                    id="kc-form-login"
                                    onSubmit={() => {
                                        setIsLoginButtonDisabled(true);
                                        return true;
                                    }}
                                    action={url.loginAction}
                                    method="post"
                                >
                                    {!usernameHidden && (
                                        <React.Fragment>
                                            <TextField
                                                id="username"
                                                name="username"
                                                defaultValue={login.username ?? ""}
                                                label={userNameLabelText}
                                                type="text"
                                                autoFocus
                                                autoComplete="username"
                                                error={userNameHasError}
                                                helperText={userNameHasError ? <span dangerouslySetInnerHTML={{ __html: errorHtml }} /> : ""}
                                                tabIndex={2}
                                                aria-invalid={userNameHasError}
                                                fullWidth
                                            />
                                        </React.Fragment>
                                    )}
                                    <Box sx={{m: "1em"}}></Box>

                                    <PasswordWrapper i18n={i18n} passwordInputId="password">
                                        <TextField
                                            id="password"
                                            name="password"
                                            type="password"
                                            label={msg("password")}
                                            autoComplete="current-password"
                                            tabIndex={3}
                                            aria-invalid={userNameHasError}
                                            error={userNameHasError}
                                            helperText={
                                                usernameHidden && userNameHasError ? <span dangerouslySetInnerHTML={{ __html: errorHtml }} /> : ""
                                            }
                                            fullWidth
                                        />
                                    </PasswordWrapper>

                                    <CardActions id="kc-form-buttons">
                                        <input type="hidden" id="id-hidden-input" name="credentialId" value={auth.selectedCredential} />
                                        <Button
                                            name="login"
                                            id="kc-login"
                                            tabIndex={7}
                                            type="submit"
                                            variant={"contained"}
                                            disabled={isLoginButtonDisabled}
                                        >
                                            {msgStr("doLogIn")}
                                        </Button>

                                        <div id="kc-form-options">
                                            {realm.rememberMe && !usernameHidden && (
                                                <FormControlLabel
                                                    control={
                                                        <Checkbox
                                                            tabIndex={8}
                                                            id="rememberMe"
                                                            name="rememberMe"
                                                            defaultChecked={!!login.rememberMe}
                                                        />
                                                    }
                                                    label={msg("rememberMe")}
                                                />
                                            )}

                                            {realm.resetPasswordAllowed && (
                                                <Button tabIndex={6} href={url.loginResetCredentialsUrl}>
                                                    {msg("doForgotPassword")}
                                                </Button>
                                            )}
                                        </div>
                                    </CardActions>
                                </form>
                            )}
                        </div>
                    </Card>
                    {newUserComponent}
                </Container>
            </Template>
        </>
    );
}
