
import { useNotification } from "./NotificationContext";
import { useNavigate } from "react-router-dom";

export const useFetchPlus = () => {
    const { showNotification } = useNotification();
    const navigate = useNavigate();

    return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const response = await fetch(input, init);

        if (response.status === 401 || response.status === 403) {
            showNotification("Session expired. Please log in again.", "error");
            navigate("/user-account");
            throw new Error("Unauthorized");
        }

        return response;
    };
};
