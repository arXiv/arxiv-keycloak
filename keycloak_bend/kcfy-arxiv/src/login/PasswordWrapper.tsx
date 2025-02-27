import type { JSX } from "keycloakify/tools/JSX";
import React from "react";
import { useIsPasswordRevealed } from "keycloakify/tools/useIsPasswordRevealed";
import type { I18n } from "./i18n";
import Box from "@mui/material/Box";
import IconButton from '@mui/material/IconButton';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';


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

export default PasswordWrapper;
