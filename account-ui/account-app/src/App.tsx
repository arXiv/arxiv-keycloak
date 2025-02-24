import React, {useEffect} from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {RuntimeContextProvider} from "./RuntimeContext";
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
// import Login from "./pages/Login";
import Logout from "./pages/Logout";
import AccountRegistration from "./pages/AccountRegistration.tsx";

import ArxivHeader from "./components/ArxivHeader";
import {Box, Container} from "@mui/material";
import ArxivFooter from "./components/ArxivFooter.tsx";
import AccountSettings from "./pages/AccountSettings.tsx";
import OwnershipRequest from "./pages/OwnershipRequest.tsx";
import NotFound404 from "./components/NotFound404.tsx";
import AuthorshipStatus from "./pages/AuthorshipStatus.tsx";

const queryClient = new QueryClient();

const App: React.FC = () => {

    const ExternalRedirect = ({ to }) => {
        useEffect(() => {
            // This causes a full page reload to the given URL.
            window.location.replace(to);
        }, [to]);

        return null;
    };

    return (
        <QueryClientProvider client={queryClient}>
        <RuntimeContextProvider>
            <Box sx={{minHeight: '100vh', backgroundColor: 'white', display: 'flex', flexDirection: 'column'}}>
                <Router>
                    <ArxivHeader />
                    <Container component="main">
                        <Routes>
                            <Route path="/user" element={<AccountSettings />} />
                            <Route path="/user/login" element={<ExternalRedirect to={"/login"} />} />
                            <Route path="/user/logout" element={<Logout />} />
                            <Route path="/user/register" element={<AccountRegistration />} />
                            <Route path="/user/ownership-request" element={<OwnershipRequest />} />
                            <Route path="/user/change-author-status" element={<AuthorshipStatus />} />
                            <Route path="*" element={<NotFound404 />} />
                        </Routes>
                    </Container>
                    <ArxivFooter />
                </Router>
            </Box>
        </RuntimeContextProvider>
        </QueryClientProvider>
    );
}

export default App;
