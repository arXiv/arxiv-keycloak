import type { JSX } from "keycloakify/tools/JSX";
import { useState } from "react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import { useIsPasswordRevealed } from "keycloakify/tools/useIsPasswordRevealed";
import { clsx } from "keycloakify/tools/clsx";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import { getKcClsx, type KcClsx } from "keycloakify/login/lib/kcClsx";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import Link from "@mui/material/Link";
import TextField from "@mui/material/TextField";
import { CardActions, CardHeader } from "@mui/material";

export default function Login(props: PageProps<Extract<KcContext, { pageId: "login.ftl" }>, I18n>) {
    const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

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
            infoNode={
                <div id="kc-registration-container">
                    <div id="kc-registration">
                        <span>
                            {msg("noAccount")}{" "}
                            <a tabIndex={8} href={url.registrationUrl}>
                                {msg("doRegister")}
                            </a>
                        </span>
                    </div>
                </div>
            }
            socialProvidersNode={
                <>
                    {realm.password && social?.providers !== undefined && social.providers.length !== 0 && (
                        <div id="kc-social-providers" className={kcClsx("kcFormSocialAccountSectionClass")}>
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
            <Container maxWidth="sm" sx={{ mt: 2 }}>
                <Typography variant={"h5"}>Login to arXiv.org</Typography>
                {/* Privacy Policy Notice */}
                <Card elevation={3} sx={{ p: 3, mb: 3, backgroundColor: "#eeeef8" }}>
                    <Typography variant="body1" fontWeight={"bold"} color="textSecondary" align="left">
                        {"The "}
                        <Link href="https://arxiv.org/help/policies/privacy_policy" target="_blank" rel="noopener" underline="hover">
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
                        <Typography variant={"h5"} sx={{mb: 2, width: "100%", textAlign: "center"}}>Login to arXiv.org</Typography>
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
                                <div className={kcClsx("kcFormGroupClass")}>

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
                                        inputProps={{
                                            tabIndex: 2,
                                            "aria-invalid": userNameHasError,
                                        }}
                                        fullWidth
                                    />
                                </div>
                            )}

                            <TextField
                                id="password"
                                name="password"
                                type="password"
                                label={msg("password")}
                                variant="outlined"
                                autoComplete="current-password"
                                inputProps={{
                                    tabIndex: 3,
                                    "aria-invalid": userNameHasError,
                                }}
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

                            <CardActions>
                                    {realm.rememberMe && !usernameHidden && (
                                        <div className="checkbox">
                                            <label>
                                                <input
                                                    tabIndex={5}
                                                    id="rememberMe"
                                                    name="rememberMe"
                                                    type="checkbox"
                                                    defaultChecked={!!login.rememberMe}
                                                />{" "}
                                                {msg("rememberMe")}
                                            </label>
                                        </div>
                                    )}

                                    {
                                        realm.resetPasswordAllowed && (
                                            <Button tabIndex={6} href={url.loginResetCredentialsUrl}>
                                                {msg("doForgotPassword")}
                                            </Button>
                                    )
                                    }

                                <input type="hidden" id="id-hidden-input" name="credentialId" value={auth.selectedCredential} />
                                <Button name="login" id="kc-login" tabIndex={7} type="submit" variant={"contained"} disabled={isLoginButtonDisabled} >
                                    {msgStr("doLogIn")}
                                </Button>
                            </CardActions>
                        </form>
                    )}
                </Card>
            </Container>
        </Template>
        </>
    );
}

function PasswordWrapper(props: { kcClsx: KcClsx; i18n: I18n; passwordInputId: string; children: JSX.Element }) {
    const { kcClsx, i18n, passwordInputId, children } = props;

    const { msgStr } = i18n;

    const { isPasswordRevealed, toggleIsPasswordRevealed } = useIsPasswordRevealed({ passwordInputId });

    return (
        <div className={kcClsx("kcInputGroup")}>
            {children}
            <button
                type="button"
                className={kcClsx("kcFormPasswordVisibilityButtonClass")}
                aria-label={msgStr(isPasswordRevealed ? "hidePassword" : "showPassword")}
                aria-controls={passwordInputId}
                onClick={toggleIsPasswordRevealed}
            >
                <i className={kcClsx(isPasswordRevealed ? "kcFormPasswordVisibilityIconHide" : "kcFormPasswordVisibilityIconShow")} aria-hidden />
            </button>
        </div>
    );
}
