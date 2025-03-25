import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useNotification } from "./NotificationContext";


export const fetchPlus = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const response = await fetch(input, init);

    if (response.status === 401 || response.status === 403) {
        window.dispatchEvent(new CustomEvent("unauthorized", {
            detail: { message: "Session expired. Please log in again." }
        }));
        throw new Error("Unauthorized");
    }

    return response;
};

export const GlobalAuthHandler = () => {
    const navigate = useNavigate();
    const { showNotification } = useNotification();

    useEffect(() => {
        const handler = (event: Event) => {
            const custom = event as CustomEvent;
            showNotification(custom.detail.message, "error");
            navigate("/user-account");
        };

        window.addEventListener("unauthorized", handler);
        return () => window.removeEventListener("unauthorized", handler);
    }, [navigate, showNotification]);

    return null;
};