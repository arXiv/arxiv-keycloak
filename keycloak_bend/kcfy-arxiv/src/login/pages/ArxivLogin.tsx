import type { JSX } from "keycloakify/tools/JSX";
import React, { useState } from "react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import { useIsPasswordRevealed } from "keycloakify/tools/useIsPasswordRevealed";
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
import IconButton from '@mui/material/IconButton';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
// import  CardHeader from "@mui/material/CardHeader";

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
    const errorHtml = userNameHasError
        ? kcSanitize(messagesPerField.getFirstError("username", "password"))
        : '';

    const newUserPanel = (
        <Container  maxWidth="sm" sx={{ p: 3, mt: 2 }}>
            <Typography variant="h2"  gutterBottom>
                {"If you've never logged in to arXiv.org"}
            </Typography>
        <Box id="kc-registration-container">
            <div id="kc-registration">
                <Button tabIndex={8}  variant="contained" color="primary" onClick={() => {
                    window.location.href = url.registrationUrl
                }}
                >
                    {"Register for the first time"}
                </Button>

                <Typography variant="h6" component="div" maxWidth={"30rem"}>
                    Registration is required to submit or update papers, but is not necessary to view them.
                </Typography>
            </div>
        </Box>
        </Container>

    );

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
                        {realm.password && social?.providers !== undefined && social.providers.length !== 0 && (
                            <div id="kc-social-providers" >
                                <hr />
                                <h2>{msg("identity-provider-login-label")}</h2>
                                <ul className={kcClsx("kcFormSocialAccountListClass", social.providers.length > 3 && "kcFormSocialAccountListGridClass")}>
                                    {social.providers.map((...[p, , providers]) => (
                                        <li key={p.alias}>
                                            <a
                                                id={`social-${p.alias}`}
                                                className={kcClsx(
                                                    "kcFormSocialAccountListButtonClass",
                                                    providers.length > 3 && "kcFormSocialAccountGridItem"
                                                )}
                                                type="button"
                                                href={p.loginUrl}
                                            >
                                                {p.iconClasses && <i className={clsx(kcClsx("kcCommonLogoIdP"), p.iconClasses)} aria-hidden="true"></i>}
                                                <span
                                                    className={clsx(kcClsx("kcFormSocialAccountNameClass"), p.iconClasses && "kc-social-icon-text")}
                                                    dangerouslySetInnerHTML={{ __html: kcSanitize(p.displayName) }}
                                                ></span>
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </>
                }
            >
                <Container id="kc-form" maxWidth="sm" sx={{ mt: 2 }}>

                    <Typography variant={"h1"} sx={{p: 2}}>Login to arXiv.org </Typography>

                    {/* Privacy Policy Notice */}
                    <Card elevation={3} sx={{ p: 3, mb: 3, backgroundColor: "#eeeef8" }}>
                        <Typography variant="body1" fontWeight={"bold"} color="textSecondary" align="left">
                            {"The "}
                            <Link href={registrationUrl}
                                  target="_blank" rel="noopener" underline="hover">
                                arXiv Privacy Policy
                            </Link>
                            {" has changed. By continuing to use arxiv.org, you are agreeing to the privacy policy."}
                        </Typography>
                    </Card>

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
                                variant="h2"
                                sx={{
                                    backgroundColor: 'white',
                                    px: 2,
                                    zIndex: 1, // Ensure the text is above the border
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
                                        <Typography variant={"h5"} sx={{p: 1}}>
                                            {userNameLabelText}
                                        </Typography>
                                        <TextField
                                            id="username"
                                            name="username"
                                            defaultValue={login.username ?? ""}
                                            label={userNameLabelText}
                                            type="text"
                                            variant="outlined"
                                            autoFocus
                                            autoComplete="username"
                                            error={userNameHasError}
                                            helperText={
                                                userNameHasError ? <span dangerouslySetInnerHTML={{ __html: errorHtml }} /> : ""
                                            }
                                            tabIndex={2}
                                            aria-invalid={userNameHasError}
                                            fullWidth
                                        />
                                    </React.Fragment>
                                )}

                                <Typography variant={"h5"} sx={{p: 1}}>{msg("password")}</Typography>
                                <PasswordWrapper  i18n={i18n} passwordInputId="password">
                                    <TextField
                                        id="password"
                                        name="password"
                                        type="password"
                                        label={msg("password")}
                                        variant="outlined"
                                        autoComplete="current-password"
                                        tabIndex={3}
                                        aria-invalid={userNameHasError}
                                        error={userNameHasError}
                                        helperText={
                                            usernameHidden && userNameHasError ? (
                                                <span dangerouslySetInnerHTML={{ __html: errorHtml }} />
                                            ) : (
                                                ""
                                            )
                                        }
                                        fullWidth
                                    />
                                </PasswordWrapper>

                                <CardActions>
                                    <div id="kc-form-buttons" >
                                        <input type="hidden" id="id-hidden-input" name="credentialId" value={auth.selectedCredential} />
                                        <Button name="login" id="kc-login" tabIndex={7} type="submit" variant={"contained"} disabled={isLoginButtonDisabled} >
                                            {msgStr("doLogIn")}
                                        </Button>
                                    </div>

                                    <div id="kc-form-options">
                                        {realm.rememberMe && !usernameHidden && (
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        tabIndex={5}
                                                        id="rememberMe"
                                                        name="rememberMe"
                                                        defaultChecked={!!login.rememberMe}
                                                    />
                                                }
                                                label={msg("rememberMe")}
                                            />
                                        )}

                                        {
                                            realm.resetPasswordAllowed && (
                                                <Button tabIndex={6} href={url.loginResetCredentialsUrl}>
                                                    {msg("doForgotPassword")}
                                                </Button>
                                            )
                                        }
                                    </div>

                                </CardActions>
                            </form>
                        )}
                        </div>
                    </Card>
                </Container>
            </Template>
        </>
    );
}

/* eslint-disable react/prop-types */
const PasswordWrapper: React.FC<{i18n: I18n, passwordInputId: string, children: JSX.Element}> = ({i18n, passwordInputId, children}) => {
    const { msgStr } = i18n;
    const { isPasswordRevealed, toggleIsPasswordRevealed } = useIsPasswordRevealed({ passwordInputId });

    return (
        <Box display="flex" alignItems="center">
            {children}
            <IconButton
                onClick={toggleIsPasswordRevealed}
                aria-label={msgStr(isPasswordRevealed ? "hidePassword" : "showPassword")}
                aria-controls={passwordInputId}
            >
                {isPasswordRevealed ? <VisibilityOff /> : <Visibility />}
            </IconButton>
        </Box>
    );
};