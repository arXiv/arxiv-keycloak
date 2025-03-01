import React, { createContext, useContext, useState, ReactNode } from "react";

import { Snackbar, Alert } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import Typography from "@mui/material/Typography";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";

type NotificationType = "success" | "error" | "info" | "warning";

interface NotificationState {
    message: string;
    type: NotificationType;
    open: boolean;
}

interface NotificationContextType {
    showNotification: (message: string, type: NotificationType) => void;
    showMessageDialog: (message: string, title: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);


interface MessageDialogState {
    title: string;
    message: string;
    open: boolean;
    onClose?: () => void;
    onConfirm?: () => void;
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

    const showMessageDialog = (message: string, title: string) => {
        setMessageDialog({message: message, title: title, open: true});
    }

    const handleMessageDialogClose = () => {
        setMessageDialog((prev) => ({...prev, open: false}));
    }

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
                        <Button onClick={handleMessageDialogClose} color="primary">Okay</Button>
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


