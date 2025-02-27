import type { JSX } from "keycloakify/tools/JSX";
import { useState } from "react";
import type { LazyOrNot } from "keycloakify/tools/LazyOrNot";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import type { UserProfileFormFieldsProps } from "keycloakify/login/UserProfileFormFieldsProps";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
// import PasswordWrapper from "./PasswordWrapper.tsx";
// import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
// import Box from "@mui/material/Box";
// import CardActions from "@mui/material/CardActions";
// import Button from "@mui/material/Button";
import CardHeader from "@mui/material/CardHeader";
// import Checkbox from "@mui/material/Checkbox";
// import FormControlLabel from "@mui/material/FormControlLabel";

type LoginUpdateProfileProps = PageProps<Extract<KcContext, { pageId: "login-update-profile.ftl" }>, I18n> & {
    UserProfileFormFields: LazyOrNot<(props: UserProfileFormFieldsProps) => JSX.Element>;
    doMakeUserConfirmPassword: boolean;
};

export default function LoginUpdateProfile(props: LoginUpdateProfileProps) {
    const { kcContext, i18n, doUseDefaultCss, Template, classes, UserProfileFormFields, doMakeUserConfirmPassword } = props;

    const { kcClsx } = getKcClsx({
        doUseDefaultCss,
        classes
    });

    const { messagesPerField, url, isAppInitiatedAction } = kcContext;

    const { msg, msgStr } = i18n;

    const [isFormSubmittable, setIsFormSubmittable] = useState(false);

    return (
        <Template
            kcContext={kcContext}
            i18n={i18n}
            doUseDefaultCss={doUseDefaultCss}
            classes={classes}

            headerNode={null}
            displayMessage={messagesPerField.exists("global")}
        >
            <Container id="kc-form" maxWidth="sm" sx={{ mt: 2 }}>
                <Card
                    elevation={2}
                    sx={{
                        p: 1,
                        b: 1
                    }}
                >
                    <CardHeader title={msg("loginProfileTitle")} slotProps={{ title: { fontSize: "1.8rem" } }} />
                    <Typography variant="subtitle2" color="textSecondary">
                        <span className="required">*</span> {msg("requiredFields")}
                    </Typography>

                    <form id="kc-update-profile-form" className={kcClsx("kcFormClass")} action={url.loginAction} method="post">
                        {
                        /*

                         */
                        }
                        <UserProfileFormFields
                            kcContext={kcContext}
                            i18n={i18n}
                            kcClsx={kcClsx}
                            onIsFormSubmittableValueChange={setIsFormSubmittable}
                            doMakeUserConfirmPassword={doMakeUserConfirmPassword}
                        />
                        <div className={kcClsx("kcFormGroupClass")}>
                            <div id="kc-form-options" className={kcClsx("kcFormOptionsClass")}>
                                <div className={kcClsx("kcFormOptionsWrapperClass")} />
                            </div>
                            <div id="kc-form-buttons" className={kcClsx("kcFormButtonsClass")}>
                                <input
                                    disabled={!isFormSubmittable}
                                    className={kcClsx(
                                        "kcButtonClass",
                                        "kcButtonPrimaryClass",
                                        !isAppInitiatedAction && "kcButtonBlockClass",
                                        "kcButtonLargeClass"
                                    )}
                                    type="submit"
                                    value={msgStr("doSubmit")}
                                />
                                {isAppInitiatedAction && (
                                    <button
                                        className={kcClsx("kcButtonClass", "kcButtonDefaultClass", "kcButtonLargeClass")}
                                        type="submit"
                                        name="cancel-aia"
                                        value="true"
                                        formNoValidate
                                    >
                                        {msg("doCancel")}
                                    </button>
                                )}
                            </div>
                        </div>
                    </form>
                </Card>
            </Container>
        </Template>
    );
}
