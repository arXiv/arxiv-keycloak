import React, {useContext, useState, useEffect} from "react";

import { RuntimeContext } from "../RuntimeContext.tsx";
import {paths as adminApi} from "../types/admin-api";
import Typography, {TypographyProps} from "@mui/material/Typography";
import {ADMIN_COUNTRIES_URL} from "../types/admin-url.ts";

type CountriesType = adminApi[typeof ADMIN_COUNTRIES_URL]['get']['responses']['200']['content']['application/json'];

interface CountryNameProps extends TypographyProps {
    countryId: string;
}

const CountryName: React.FC<CountryNameProps> = ({ countryId, ...props }) => {
    const runtimeProps = useContext(RuntimeContext);
    const [countries, setCountries] = useState<CountriesType>();

    useEffect(() => {
        const fetchCountries = async () => {
            try {
                const getCountries = runtimeProps.adminFetcher.path(ADMIN_COUNTRIES_URL).method('get').create();
                const response = await getCountries({});
                const result: CountriesType = response.data;
                setCountries(result);
            } catch (error) {
                console.error("Failed to fetch countries", error);
            }
        };

        fetchCountries();
    }, [runtimeProps.adminFetcher]);

    let displayText = countryId;
    if (countries) {
        const country = countries.find((c) => c.id.toLowerCase() === countryId.toLowerCase());
        if (country) {
            displayText = country.country_name;
        }
    }
    return (<Typography {...props} >{displayText}</Typography>);
};

export default CountryName;
