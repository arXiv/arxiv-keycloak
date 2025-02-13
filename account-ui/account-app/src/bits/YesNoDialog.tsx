import React from "react";
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography } from "@mui/material";

interface ResendEmailDialogProps {
    title: string;
    message: string;
    open: boolean;
    onClose: () => void;
    onConfirm: () => void;
}

const YesNoDialog: React.FC<ResendEmailDialogProps> = ({ title, message, open, onClose, onConfirm }) => {
    return (
        <Dialog open={open} onClose={onClose}>
            <DialogTitle>{title}</DialogTitle>
            <DialogContent>
                <Typography>{message}</Typography>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} color="secondary">Cancel</Button>
                <Button onClick={onConfirm} color="primary" variant="contained">OK</Button>
            </DialogActions>
        </Dialog>
    );
};

export default YesNoDialog;
