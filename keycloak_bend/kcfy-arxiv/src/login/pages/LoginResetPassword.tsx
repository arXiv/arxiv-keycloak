import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import CardActions from "@mui/material/CardActions";
import Button from "@mui/material/Button";
import CardHeader from "@mui/material/CardHeader";

export default function LoginResetPassword(props: PageProps<Extract<KcContext, { pageId: "login-reset-password.ftl" }>, I18n>) {
    const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;


    const { url, realm, auth, messagesPerField } = kcContext;

    const { msg, msgStr } = i18n;

    const userNameHasError = messagesPerField.existsError("username");
    const userNameLabelText = !realm.loginWithEmailAllowed
        ? msg("username")
        : !realm.registrationEmailAsUsername
            ? msg("usernameOrEmail")
            : msg("email");

    const errorHtml = userNameHasError
        ? kcSanitize(messagesPerField.getFirstError("username"))
        : '';


    return (
        <Template
            kcContext={kcContext}
            i18n={i18n}
            doUseDefaultCss={doUseDefaultCss}
            classes={classes}
            displayInfo
            displayMessage={!messagesPerField.existsError("username")}
            infoNode={null}
            headerNode={null}
        >
            <Container  maxWidth="sm" sx={{ mt: 2 }}>

            <Card elevation={2}
                  sx={{
                      p: 1, b: 1
                  }}>
                <CardHeader title={"Password Recovery"} />
                <Box>
                    <Typography variant="body1">
                    {
                        realm.duplicateEmailsAllowed ? msg("emailInstructionUsername") : msg("emailInstruction")
                    }
                    </Typography>
                </Box>
            <form id="kc-reset-password-form" action={url.loginAction} method="post">

                <div >
                    <Typography variant="h5" fontWeight={"bold"} sx={{p:1}}>
                            {userNameLabelText}
                    </Typography>
                        <TextField
                            id="username"
                            name="username"
                            defaultValue={auth.attemptedUsername ?? ""}
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

                </div>
                <CardActions>
                    <div id="kc-form-options" >
                        <Button href={url.loginUrl}>
                            {msg("backToLogin")}
                        </Button>
                    </div>
                    <Box flexGrow={1}></Box>

                    <div id="kc-form-buttons">
                        <Button id="kc-submit" tabIndex={7} type="submit" variant={"contained"}>
                            {msgStr("doSubmit")}
                        </Button>
                            {
                            /*
                                                    <input
                            className={kcClsx("kcButtonClass", "kcButtonPrimaryClass", "kcButtonBlockClass", "kcButtonLargeClass")}
                            type="submit"
                            value=}
                        />

                             */
                            }
                    </div>
                </CardActions>
            </form>
            </Card>
            </Container>
        </Template>
    );
}
