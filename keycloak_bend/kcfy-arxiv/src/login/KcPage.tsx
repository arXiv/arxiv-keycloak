import { Suspense, lazy } from "react";
import type { ClassKey } from "keycloakify/login";
import type { KcContext } from "./KcContext";
import { useI18n } from "./i18n";
import DefaultPage from "keycloakify/login/DefaultPage";
import Template from "./Template";
import { createTheme, ThemeProvider } from "@mui/material/styles";

const theme = createTheme({
    typography: {
        fontFamily:
            "\"Open Sans\", \"Lucida Grande\", \"Helvetica Neue\", Helvetica, Arial, sans-serif",
        h1: {
            fontWeight: 600,
            fontSize: "1.75rem",
            marginBottom: "0.8rem"
        },
        h2: {
            fontWeight: 600,
            fontSize: "1.5rem"
        },
        h5: {
            fontWeight: 600,
            fontSize: "1.1rem"
        },
        h6: {
            fontWeight: 600,
            fontSize: "1rem"
        },

    }
});

const UserProfileFormFields = lazy(() => import("./UserProfileFormFields"));

const doMakeUserConfirmPassword = true;

const Login = lazy(() => import("./pages/ArxivLogin.tsx"));
const Register = lazy(() => import("./pages/Register"));
const LoginResetPassword = lazy(() => import("./pages/LoginResetPassword"));
const LoginUpdatePassword = lazy(() => import("./pages/LoginUpdatePassword"));
const LoginVerifyEmail = lazy(() => import("./pages/LoginVerifyEmail"));
const LoginUpdateProfile = lazy(() => import("./pages/LoginUpdateProfile"));
/*
+const LoginVerifyEmail = lazy(() => import("./pages/LoginVerifyEmail"));

 export default function KcPage(props: { kcContext: KcContext; }) {

     // ...

     return (
         <Suspense>
             {(() => {
                 switch (kcContext.pageId) {
                     // ...

}
})()}
</Suspense>
);
}
```
const LoginUpdateProfile = lazy(() => import("./pages/LoginUpdateProfile"));

export default function KcPage(props: { kcContext: KcContext; }) {

    // ...

    return (
        <Suspense>
            {(() => {
                switch (kcContext.pageId) {
                    // ...

                }
            })()}
        </Suspense>
    );
}
```
 */
export default function KcPage(props: { kcContext: KcContext }) {
    const { kcContext } = props;

    const { i18n } = useI18n({ kcContext });

    return (
        <ThemeProvider theme={theme}>
            <Suspense>
                {(() => {
                    switch (kcContext.pageId) {
                        case "login.ftl":
                            return (
                                <Login
                                    {...{ kcContext, i18n, classes }}
                                    Template={Template}
                                    doUseDefaultCss={false}
                                />
                            );
                        case "register.ftl":
                            return (
                                <Register
                                    {...{ kcContext, i18n, classes }}
                                    Template={Template}
                                    doUseDefaultCss={false}
                                    UserProfileFormFields={UserProfileFormFields}
                                    doMakeUserConfirmPassword={doMakeUserConfirmPassword}
                                />
                            );

                        case "login-reset-password.ftl":
                            return (
                                <LoginResetPassword
                                    {...{ kcContext, i18n, classes }}
                                    Template={Template}
                                    doUseDefaultCss={false}
                                />
                            );

                        case "login-update-password.ftl":
                            return (
                                <LoginUpdatePassword
                                    {...{ kcContext, i18n, classes }}
                                    Template={Template}
                                    doUseDefaultCss={false}
                                />
                            );

                        case "login-verify-email.ftl": return (
                            <LoginVerifyEmail
                                {...{ kcContext, i18n, classes }}
                                Template={Template}
                                doUseDefaultCss={false}
                            />
                        );

                        case "login-update-profile.ftl": return (
                            <LoginUpdateProfile
                                {...{ kcContext, i18n, classes }}
                                Template={Template}
                                doUseDefaultCss={false}
                                UserProfileFormFields={UserProfileFormFields}
                                doMakeUserConfirmPassword={doMakeUserConfirmPassword}
                            />
                        );

                        default:
                            return (
                                <DefaultPage
                                    kcContext={kcContext}
                                    i18n={i18n}
                                    classes={classes}
                                    Template={Template}
                                    doUseDefaultCss={false}
                                    UserProfileFormFields={UserProfileFormFields}
                                    doMakeUserConfirmPassword={doMakeUserConfirmPassword}
                                />
                            );
                    }
                })()}
            </Suspense>
        </ThemeProvider>
    );
}

const classes = {} satisfies { [key in ClassKey]?: string };
