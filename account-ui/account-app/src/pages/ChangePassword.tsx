import Typography from "@mui/material/Typography";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Link from "@mui/material/Link";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";

import {Link as RouterLink} from "react-router-dom";
import Tooltip from "@mui/material/Tooltip";
import PasswordRequirements from "../bits/PasswordRequirements.tsx";

const ChangePassword = () => {
    return (
        <Container maxWidth="sm" sx={{ mt: 2 }}>
            <Typography variant={"h5"}>Login to arXiv.org </Typography>

            {/* Login Form */}
            <Card elevation={0}
                  sx={{
                      p: 3,
                      position: 'relative',
                      paddingTop: '48px', // Add padding to push content down
                      marginTop: '24px', // Add margin to shift the entire card (including shadow)

                      '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: '16px', // Push the border down by 24px
                          left: 0,
                          right: 0,
                          height: '90%',
                          backgroundColor: 'transparent',
                          borderTop: '2px solid #ddd', // Add the border
                          borderLeft: '2px solid #ddd', // Add the border
                          borderRight: '2px solid #ddd', // Add the border
                          borderBottom: '2px solid #ddd', // Add the border
                      },
                  }}>

                <Box
                    sx={{
                        display: 'flex',
                        justifyContent: 'left',
                        alignItems: 'left',
                        width: '100%',
                        position: 'relative',
                        marginTop: '-44px', // Adjust this to move the title up
                        marginBottom: '16px',
                    }}
                >
                    <Typography
                        variant="h5"
                        fontWeight="normal"
                        sx={{
                            backgroundColor: 'white',
                            px: 2,
                            zIndex: 1, // Ensure the text is above the border
                        }}
                    >
                        Change Password
                    </Typography>
                </Box>

                <CardContent>
                    <Box component="form" sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Old Password"}</Typography>
                            <TextField id="old-password" label="Old Password" type="password" variant="outlined" fullWidth />
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"New Password"}</Typography>
                            <Tooltip title={<PasswordRequirements />}>
                                <TextField id="new-password" label="New Password" type="password" variant="outlined" fullWidth />
                            </Tooltip>
                        </Box>
                        <Box>
                            <Typography fontWeight={"bold"} sx={{mb: 1}}>{"Retype Password"}</Typography>
                            <Tooltip title={<PasswordRequirements />}>
                                <TextField id="password-new" label="Retype Password" type="password" variant="outlined" fullWidth />
                            </Tooltip>
                        </Box>

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Button variant="contained" sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": { backgroundColor: "#1420c0"
                                } }}>
                                Submit
                            </Button>
                        </Box>
                    </Box>
                </CardContent>
            </Card>
        </Container>
    );
};

export default ChangePassword;