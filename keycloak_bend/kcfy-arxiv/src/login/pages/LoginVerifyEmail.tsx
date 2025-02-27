import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import Container from "@mui/material/Container";
// import Typography from "@mui/material/Typography";
// import PasswordWrapper from "./PasswordWrapper.tsx";
// import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
// import Box from "@mui/material/Box";
// import CardActions from "@mui/material/CardActions";
// import Button from "@mui/material/Button";
import CardHeader from "@mui/material/CardHeader";
// import Checkbox from "@mui/material/Checkbox";
// import FormControlLabel from "@mui/material/FormControlLabel";

export default function LoginVerifyEmail(props: PageProps<Extract<KcContext, { pageId: "login-verify-email.ftl" }>, I18n>) {
    const { kcContext, i18n, doUseDefaultCss, Template, classes } = props;

    const { msg } = i18n;

    const { url, user } = kcContext;

    return (
        <Template
            kcContext={kcContext}
            i18n={i18n}
            doUseDefaultCss={doUseDefaultCss}
            classes={classes}
            displayInfo
            headerNode={null}
            infoNode={null}
        >
            <Container maxWidth="sm" sx={{ mt: 2 }}>
                <Card elevation={2} sx={{ p: 1, b: 1 }}>
                    <CardHeader title={msg("emailVerifyTitle")} slotProps={{ title: { fontSize: "1.8rem" } }} />

                    <p className="instruction">
                        {msg("emailVerifyInstruction2")}
                        <br />
                        <a href={url.loginAction}>{msg("doClickHere")}</a>
                        &nbsp;
                        {msg("emailVerifyInstruction3")}
                    </p>

                    <p className="instruction">{msg("emailVerifyInstruction1", user?.email ?? "")}</p>
                </Card>
            </Container>
        </Template>
    );
}
