import React from "react";
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

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
