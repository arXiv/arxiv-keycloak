import React, {useEffect} from "react";
import {QueryClient, QueryClientProvider} from "@tanstack/react-query";
import {RuntimeContextProvider} from "./RuntimeContext";
import {BrowserRouter as Router, Routes, Route} from "react-router-dom";

import {NotificationProvider} from "./NotificationContext";


// import Login from "./pages/Login";
import Logout from "./pages/Logout";
import AccountRegistration from "./pages/AccountRegistration.tsx";

import ArxivHeader from "./components/ArxivHeader";
import {Box, Container} from "@mui/material";
import ArxivFooter from "./components/ArxivFooter.tsx";
import UserAccountInfo from "./pages/UserAccountInfo.tsx";
import OwnershipRequest from "./pages/OwnershipRequest.tsx";
import NotFound404 from "./components/NotFound404.tsx";
import AuthorshipStatus from "./pages/AuthorshipStatus.tsx";
import UpdateProfile from "./pages/UpdateProfile.tsx";
import ChangePassword from "./pages/ChangePassword.tsx";
import ChangeEmail from "./pages/ChangeEmail.tsx";
import EnterEndorsementCode from "./pages/EnterEndorsementCode.tsx";
import YourDocuments from "./pages/YourDocuments.tsx";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import ClaimPaperOwnership from "./pages/ClaimPaperOwnership.tsx";
import ResetPassword from "./pages/ResetPassword.tsx";
import {GlobalAuthHandler} from "./fetchPlus.ts";

const queryClient = new QueryClient();

const App: React.FC = () => {

    const ExternalRedirect: React.FC<{ to: string }> = ({to}) => {
        useEffect(() => {
            // This causes a full page reload to the given URL.
            window.location.replace(to);
        }, [to]);

        return null;
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs} >
        <QueryClientProvider client={queryClient}>
            <NotificationProvider>
                <RuntimeContextProvider>
                    <Box sx={{minHeight: '100vh', backgroundColor: 'white', display: 'flex', flexDirection: 'column'}}>
                        <Router>
                            <GlobalAuthHandler />
                            <ArxivHeader/>
                            <Container component="main">
                            <Routes>
                                <Route path="/user-account" element={<UserAccountInfo/>}/>
                                <Route path="/user-account/login" element={<ExternalRedirect to={"/login"}/>}/>
                                <Route path="/user-account/logout" element={<Logout/>}/>
                                <Route path="/user-account/register" element={<AccountRegistration/>}/>
                                <Route path="/user-account/request-document-ownership" element={<OwnershipRequest/>}/>
                                <Route path="/user-account/change-author-status" element={<AuthorshipStatus/>}/>
                                <Route path="/user-account/update-profile" element={<UpdateProfile/>}/>
                                <Route path="/user-account/change-password" element={<ChangePassword/>}/>
                                <Route path="/user-account/change-email" element={<ChangeEmail/>}/>
                                <Route path="/user-account/endorse" element={<EnterEndorsementCode/>}/>
                                <Route path="/user-account/owned-documents" element={<YourDocuments/>}/>
                                <Route path="/user-account/claim-document-ownership" element={<ClaimPaperOwnership/>}/>
                                <Route path="/user-account/reset-password" element={<ResetPassword />}/>
                                <Route path="*" element={<NotFound404/>}/>
                            </Routes>
                        </Container>
                            <ArxivFooter/>
                        </Router>
                    </Box>
                </RuntimeContextProvider>
            </NotificationProvider>
        </QueryClientProvider>
        </LocalizationProvider>
    );
}

export default App;
