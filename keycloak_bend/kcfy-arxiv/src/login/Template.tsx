import React from 'react';
import { useEffect } from "react";
// import { clsx } from "keycloakify/tools/clsx";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { TemplateProps } from "keycloakify/login/TemplateProps";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import { useSetClassName } from "keycloakify/tools/useSetClassName";
import { useInitialize } from "keycloakify/login/Template.useInitialize";
import type { I18n } from "./i18n";
import type { KcContext } from "./KcContext";
import ArxivHeader from "../components/ArxivHeader.tsx";
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ArxivFooter from "../components/ArxivFooter.tsx";
import Box from '@mui/material/Box';
// import Card from '@mui/material/Card';
import Alert from '@mui/material/Alert';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Link from '@mui/material/Link';
import IconButton from '@mui/material/IconButton';
import RestartAltIcon from "@mui/icons-material/RestartAlt";


interface LocaleDropdownProps {
    i18n: I18n;
}

const LocaleDropdown: React.FC<LocaleDropdownProps> = ({ i18n }) => {
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleClose = () => {
        setAnchorEl(null);
    };

    return (
        <div>
            <Button
                id="kc-current-locale-link"
                aria-controls={open ? 'language-switch1' : undefined}
                aria-haspopup="true"
                aria-expanded={open ? 'true' : undefined}
                onClick={handleClick}
            >
                {i18n.currentLanguage.label}
            </Button>
            <Menu
                id="language-switch1"
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                MenuListProps={{
                    'aria-labelledby': 'kc-current-locale-link',
                }}
            >
                {i18n.enabledLanguages.map(({ languageTag, label, href }) => (
                    <MenuItem
                        key={languageTag}
                        onClick={() => {
                            handleClose();
                            // Navigate to the new language href
                            window.location.href = href;
                        }}
                    >
                        {label}
                    </MenuItem>
                ))}
            </Menu>
        </div>
    );
};

export default function Template(props: TemplateProps<KcContext, I18n>) {
    const {
        displayInfo = false,
        displayMessage = true,
        displayRequiredFields = false,
        headerNode,
        socialProvidersNode = null,
        infoNode = null,
        documentTitle,
        bodyClassName,
        kcContext,
        i18n,
        doUseDefaultCss,
        classes,
        children
    } = props;

    const { kcClsx } = getKcClsx({ doUseDefaultCss, classes });

    const { msg, msgStr, enabledLanguages } = i18n;

    const { auth, url, message, isAppInitiatedAction } = kcContext;

    useEffect(() => {
        document.title = documentTitle ?? msgStr("loginTitle", kcContext.realm.displayName);
    }, []);

    useSetClassName({
        qualifiedName: "html",
        className: kcClsx("kcHtmlClass")
    });

    useSetClassName({
        qualifiedName: "body",
        className: bodyClassName ?? kcClsx("kcBodyClass")
    });

    const { isReadyToRender } = useInitialize({ kcContext, doUseDefaultCss });

    if (!isReadyToRender) {
        return null;
    }


    return (
        <Box sx={{minHeight: '100vh', backgroundColor: 'white', display: 'flex', flexDirection: 'column'}}>
            <ArxivHeader />
            <div className={kcClsx("kcFormCardClass")}>
                <header>
                    {enabledLanguages.length > 1 && <LocaleDropdown i18n={i18n} />}

                    {auth?.showUsername && !auth?.showResetCredentials ? (
                        <Container maxWidth="sm" >
                            <Box display="flex" alignItems="center" gap={1}>
                            <Typography id="kc-attempted-username" variant="subtitle1">
                                {auth.attemptedUsername}
                            </Typography>
                            <Tooltip title={msgStr("restartLoginTooltip")}>
                                <Link id="reset-login" href={url.loginRestartFlowUrl} aria-label={msgStr("restartLoginTooltip")}>
                                    <IconButton size="small">
                                        <RestartAltIcon />
                                        {msgStr("restartLoginTooltip")}
                                    </IconButton>
                                </Link>
                            </Tooltip>
                        </Box>
                        </Container>
                    ) : (
                        <Typography id="kc-page-title" variant="h5">
                            {headerNode}
                        </Typography>
                    )}

                    {displayRequiredFields && (
                        <Box mt={2}>
                            <Typography variant="subtitle2" color="textSecondary">
                                <span className="required">*</span> {msg("requiredFields")}
                            </Typography>
                        </Box>
                    )}
                </header>
                <div id="kc-content">
                    <div id="kc-content-wrapper">
                        {/* App-initiated actions should not see warning messages about the need to complete the action during login. */}
                        {displayMessage && message !== undefined && (message.type !== "warning" || !isAppInitiatedAction) && (
                            <Container maxWidth="sm" sx={{ p: 3, mt: 2 }}>
                                <Alert security={message.type}>
                                    {kcSanitize(message.summary)}
                                </Alert>
                            </Container>
                        )}
                        {children}
                        {auth !== undefined && auth.showTryAnotherWayLink && (
                            <form id="kc-select-try-another-way-form" action={url.loginAction} method="post">
                                <div className={kcClsx("kcFormGroupClass")}>
                                    <input type="hidden" name="tryAnotherWay" value="on" />
                                    <a
                                        href="#"
                                        id="try-another-way"
                                        onClick={() => {
                                            document.forms["kc-select-try-another-way-form" as never].submit();
                                            return false;
                                        }}
                                    >
                                        {msg("doTryAnotherWay")}
                                    </a>
                                </div>
                            </form>
                        )}
                        <Container maxWidth="sm" >
                            {socialProvidersNode}
                        </Container>
                        {displayInfo && (
                            <div id="kc-info" className={kcClsx("kcSignUpClass")}>
                                <div id="kc-info-wrapper" className={kcClsx("kcInfoAreaWrapperClass")}>
                                    {infoNode}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <Box sx={{flex: 1}}/>
            <ArxivFooter />
        </Box>
    );
}
