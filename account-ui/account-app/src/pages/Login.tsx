import Typography from "@mui/material/Typography";
import Button  from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Link from "@mui/material/Link";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";

import {Link as RouterLink} from "react-router-dom";

const Login = () => {
    return (
        <Container maxWidth="sm" sx={{ mt: 2 }}>
            <Typography variant={"h5"}>Login to arXiv.org </Typography>
            {/* Privacy Policy Notice */}
            <Card elevation={3} sx={{ p: 3, mb: 3, backgroundColor: "#eeeef8" }}>
                <Typography variant="body1" fontWeight={"bold"} color="textSecondary" align="left">
                    {"The "}
                    <Link href="https://arxiv.org/help/policies/privacy_policy" target="_blank" rel="noopener" underline="hover">
                        arXiv Privacy Policy
                    </Link>
                    {" has changed. By continuing to use arxiv.org, you are agreeing to the privacy policy."}
                </Typography>
            </Card>

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
                        If you're already registered
                    </Typography>
                </Box>

                <CardContent>
                    <Box component="form" sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <TextField label="Username or e-mail" variant="outlined" fullWidth />
                        <TextField label="Password" type="password" variant="outlined" fullWidth />

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Button variant="contained" sx={{
                                backgroundColor: "#1976d2",
                                "&:hover": { backgroundColor: "#1420c0"
                                } }}>
                                Submit
                            </Button>
                            <Link href="/password-recovery" variant="body2">
                                Forgot your password?
                            </Link>
                        </Box>
                    </Box>
                </CardContent>
            </Card>

            {/* Registration Information */}
            <Container sx={{ p: 3, mt: 3 }}>
                <Typography variant="h5" fontWeight="bold" gutterBottom>
                    If you've never logged in to arXiv.org
                </Typography>
                <Button
                    component={RouterLink}
                    to="/user/register"
                    variant="contained"
                    sx={{
                        backgroundColor: "#1976d2",
                        color: "white",
                        "&:hover": {
                            backgroundColor: "#1420c0",
                            color: "white",
                        },
                        textTransform: "none", // Keeps text casing as written
                    }}
                >
                    Register for the first time
                </Button>
                <Typography variant="body1" color="textSecondary" sx={{ mt: 2, mb: 1 }}>
                    Registration is required to submit or update papers, but is not necessary to view them.
                </Typography>
            </Container>
        </Container>
    );
};

export default Login;