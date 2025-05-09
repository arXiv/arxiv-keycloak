import React, {useContext, useState, useEffect} from "react";

import { RuntimeContext } from "../RuntimeContext.tsx";
import {paths as adminApi} from "../types/admin-api";
import Typography, {TypographyProps} from "@mui/material/Typography";

type CountriesType = adminApi['/v1/countries/iso2']['get']['responses']['200']['content']['application/json'];

interface CountryNameProps extends TypographyProps {
    countryId: string;
}

const CountryName: React.FC<CountryNameProps> = ({ countryId, ...props }) => {
    const runtimeProps = useContext(RuntimeContext);
    const [countries, setCountries] = useState<CountriesType>();

    useEffect(() => {
        const fetchCountries = async () => {
            try {
                const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/countries/iso2`);
                const result: CountriesType = await response.json();
                setCountries(result);
            } catch (error) {
                console.error("Failed to fetch group info", error);
            }
        };

        fetchCountries();
    }, [runtimeProps.ADMIN_API_BACKEND_URL]);

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
