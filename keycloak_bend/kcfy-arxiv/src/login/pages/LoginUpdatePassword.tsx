import { kcSanitize } from "keycloakify/lib/kcSanitize";
import { getKcClsx, type KcClsx } from "keycloakify/login/lib/kcClsx";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import PasswordWrapper from "../PasswordWrapper.tsx";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import Box from "@mui/material/Box";
import CardActions from "@mui/material/CardActions";
import Button from "@mui/material/Button";
import CardHeader from "@mui/material/CardHeader";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";

export default function LoginUpdatePassword(
    props: PageProps<
        Extract<
            KcContext,
            {
                pageId: "login-update-password.ftl";
            }
        >,
        I18n
    >
) {
    const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

    const { kcClsx } = getKcClsx({
        doUseDefaultCss,
        classes
    });

    const { msg, msgStr } = i18n;

    const { url, messagesPerField, isAppInitiatedAction } = kcContext;

    return (
        <Template
            kcContext={kcContext}
            i18n={i18n}
            doUseDefaultCss={doUseDefaultCss}
            classes={classes}
            displayMessage={!messagesPerField.existsError("password", "password-confirm")}
            headerNode={null}
        >
            <Container id="kc-form" maxWidth="sm" sx={{ mt: 2 }}>
                <Card
                    elevation={2}
                    sx={{
                        p: 1,
                        b: 1
                    }}
                >
                    <CardHeader title={msg("updatePasswordTitle")} slotProps={{ title: { fontSize: "1.8rem" } }} />
                    <form id="kc-passwd-update-form" action={url.loginAction} method="post">
                        <div>
                            <Typography variant={"h5"} sx={{ p: 1 }}>
                                {msg("passwordNew")}
                            </Typography>

                            <PasswordWrapper i18n={i18n} passwordInputId="password-new">
                                <TextField
                                    id="password-new"
                                    name="password-new"
                                    type="password"
                                    label={msg("password")}
                                    variant="outlined"
                                    autoComplete="new-password"
                                    tabIndex={3}
                                    aria-invalid={messagesPerField.existsError("password", "password-confirm")}
                                    helperText={kcSanitize(messagesPerField.get("password"))}
                                    fullWidth
                                />
                                {/*
                                <input
                                    type="password"
                                    id="password-new"
                                    name="password-new"
                                    className={kcClsx("kcInputClass")}
                                    autoFocus
                                    autoComplete="new-password"
                                    aria-invalid={messagesPerField.existsError("password", "password-confirm")}
                                />
    
                            {messagesPerField.existsError("password") && (
                                <span
                                    id="input-error-password"
                                    aria-live="polite"
                                    dangerouslySetInnerHTML={{
                                        __html: kcSanitize(messagesPerField.get("password"))
                                    }}
                                />
                            )}
                                     */}
                            </PasswordWrapper>
                        </div>

                        <div>
                            <Typography variant={"h5"} sx={{ p: 1 }}>
                                {msg("passwordConfirm")}
                            </Typography>
                            <PasswordWrapper i18n={i18n} passwordInputId="password-confirm">
                                {
                                    <TextField
                                        id="password-confirm"
                                        name="password-confirm"
                                        type="password"
                                        label={msg("password")}
                                        variant="outlined"
                                        autoComplete="new-password"
                                        tabIndex={4}
                                        aria-invalid={messagesPerField.existsError("password", "password-confirm")}
                                        helperText={kcSanitize(messagesPerField.get("password-confirm"))}
                                        fullWidth
                                    />

                                    /*
                                <input
                                    type="password"
                                    id="password-confirm"
                                    name="password-confirm"
                                    className={kcClsx("kcInputClass")}
                                    autoFocus
                                    autoComplete="new-password"
                                    aria-invalid={messagesPerField.existsError("password", "password-confirm")}
                                />
    
                                     */
                                }
                            </PasswordWrapper>

                            {/*
                            {messagesPerField.existsError("password-confirm") && (
                                <span
                                    id="input-error-password-confirm"
                                    className={kcClsx("kcInputErrorMessageClass")}
                                    aria-live="polite"
                                    dangerouslySetInnerHTML={{
                                        __html: kcSanitize(messagesPerField.get("password-confirm"))
                                    }}
                                />
                            )}
    
                                 */}
                        </div>
                        <CardActions id="kc-form-buttons">
                            <LogoutOtherSessions kcClsx={kcClsx} i18n={i18n} />
                            {/*
                            <input
                                className={kcClsx(
                                    "kcButtonClass",
                                    "kcButtonPrimaryClass",
                                    !isAppInitiatedAction && "kcButtonBlockClass",
                                    "kcButtonLargeClass"
                                )}
                                type="submit"
                                value={msgStr("doSubmit")}
                            />
    
                                 */}
                            <Box flexGrow={5} />
                            <Button tabIndex={6} type="submit" variant={"contained"}>
                                {msgStr("doSubmit")}
                            </Button>

                            {isAppInitiatedAction && (
                                <>
                                    {/*
                                    <button
                                        className={kcClsx("kcButtonClass", "kcButtonDefaultClass", "kcButtonLargeClass")}
                                        type="submit"
                                        name="cancel-aia"
                                        value="true"
                                    >
                                        {msg("doCancel")}
                                    </button>
        
                                         */}
                                    <Button name="cancel-aia" id="kc-login" tabIndex={7} type="submit" variant={"contained"} value="true">
                                        {msg("doCancel")}
                                    </Button>
                                </>
                            )}
                            <Box flexGrow={1} />
                        </CardActions>
                    </form>
                </Card>
            </Container>
        </Template>
    );
}

function LogoutOtherSessions(props: { kcClsx: KcClsx; i18n: I18n }) {
    const { kcClsx, i18n } = props;

    const { msg } = i18n;

    return (
        <div id="kc-form-options" className={kcClsx("kcFormOptionsClass")}>
            <div className={kcClsx("kcFormOptionsWrapperClass")}>
                {/*
                <div className="checkbox">
                    <label>
                        <input type="checkbox" id="logout-sessions" name="logout-sessions" value="on" defaultChecked={true} />
                        {msg("logoutOtherSessions")}
                    </label>
                </div>

                     */}
                <FormControlLabel
                    control={<Checkbox id="logout-sessions" name="logout-sessions" value={"on"} defaultChecked={true} />}
                    label={msg("logoutOtherSessions")}
                />
            </div>
        </div>
    );
}
