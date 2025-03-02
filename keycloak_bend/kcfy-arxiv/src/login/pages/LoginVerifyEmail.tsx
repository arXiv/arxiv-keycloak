import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { KcContext } from "../KcContext";
import type { I18n } from "../i18n";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
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
    /*
                        <CardHeader title={msg("emailVerifyTitle")} slotProps={{ title: { fontSize: "1.8rem" } }} />
     */

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
            <Container maxWidth="sm" sx={{ mt: 0 }}>
                <Card elevation={2} sx={{ py: 0, px: 2 }}>
                    <CardHeader title={"Please verify your e-mail"} slotProps={{ title: { fontSize: "1.8rem" } }} />
                    <Typography variant={"body1"} sx={{ fontSize: "1.1em", }}>
                        <p>{msg("emailVerifyInstruction2")}
                            <br />
                            <Link href={url.loginAction} sx={{fontWeight: "700"}}>{msg("doClickHere")}</Link>
                            {" "}
                            {msg("emailVerifyInstruction3")}
                        </p>
                        <p>{msg("emailVerifyInstruction1", user?.email ?? "")}</p>
                    </Typography>
                </Card>
            </Container>
        </Template>
    );
}
