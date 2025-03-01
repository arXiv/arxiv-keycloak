import React, { createContext, useContext, useState, ReactNode } from "react";

import { Snackbar, Alert } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import Typography from "@mui/material/Typography";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";

type NotificationType = "success" | "error" | "info" | "warning";

interface NotificationState {
    message: string;
    type: NotificationType;
    open: boolean;
}

interface NotificationContextType {
    showNotification: (message: string, type: NotificationType) => void;
    showMessageDialog: (message: string, title: string,
                        onClose?: () => void, onCloseLabel?: string,
                        onConfirm?: () => void, onConfirmLabel?: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);


interface MessageDialogState {
    title: string;
    message: string;
    open: boolean;
    onClose?: () => void;
    onCloseLabel?: string;
    onConfirm?: () => void;
    onConfirmLabel?: string;
}


export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [notification, setNotification] = useState<NotificationState>({
        message: "",
        type: "info",
        open: false,
    });

    const [messageDialog, setMessageDialog] = useState<MessageDialogState>({
        message: "",
        title: "",
        open: false,
    });

    const showNotification = (message: string, type: NotificationType) => {
        setNotification({ message, type, open: true });
    };

    const handleNotificationClose = () => {
        setNotification((prev) => ({ ...prev, open: false }));
    };

    const showMessageDialog = (message: string, title: string,
                               onClose?: ()=> void, onCloseLabel?: string,
                               onConfirm?: () => void, onConfirmLabel?: string) => {
        setMessageDialog({message: message, title: title, open: true, onClose, onCloseLabel, onConfirm, onConfirmLabel});
    }

    const handleMessageDialogClose = () => {
        if (messageDialog.onClose)
            messageDialog.onClose();
        setMessageDialog((prev) => ({...prev, open: false}));
    }

    const handleMessageDialogConfirm = () => {
        if (messageDialog.onConfirm)
            messageDialog.onConfirm();
        setMessageDialog((prev) => ({...prev, open: false}));
    }

    const actions =  messageDialog.onClose  && messageDialog.onConfirm ?
        (<div>
            <Button onClick={handleMessageDialogConfirm} color="primary">{messageDialog.onConfirmLabel || "Ckay"}</Button>
            <Box flexGrow={1} />
            <Button onClick={handleMessageDialogClose} color="secondary">{messageDialog.onCloseLabel || "Cancel"}</Button>
        </div>)
        : (
            <Button onClick={handleMessageDialogClose} color="primary">{messageDialog.onCloseLabel || "Ckay"}</Button>
        );

    return (
        <NotificationContext.Provider value={{ showNotification, showMessageDialog }}>
            {children}
            <Snackbar
                open={notification.open}
                autoHideDuration={3000}
                onClose={handleNotificationClose}
                anchorOrigin={{ vertical: "top", horizontal: "right" }}
            >
                <Alert onClose={handleNotificationClose} severity={notification.type} sx={{ width: "100%" }}>
                    {notification.message}
                </Alert>
            </Snackbar>

            <Dialog open={messageDialog.open} onClose={handleMessageDialogClose}>
                <DialogTitle>{messageDialog.title}</DialogTitle>
                <DialogContent>
                    <Typography>{messageDialog.message}</Typography>
                </DialogContent>
                <DialogActions>
                    {
                        actions
                    }
                </DialogActions>
            </Dialog>

        </NotificationContext.Provider>
    );
};

export const useNotification = (): NotificationContextType => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error("useNotification must be used within a NotificationProvider");
    }
    return context;
};


