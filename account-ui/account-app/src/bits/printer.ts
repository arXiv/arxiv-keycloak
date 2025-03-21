
import {User} from "../RuntimeContext";
import {paths as adminApi} from "../types/admin-api";

type EndorsementOutcomeModel = adminApi["/v1/endorsements/endorse"]['post']['responses']['200']['content']['application/json'];
type PublicUserType = EndorsementOutcomeModel["endorsee"];

export function printUserName(user: PublicUserType | User | null | undefined): string {
    if (!user)
        return "";
    return `${user?.first_name} ${user?.last_name}`;
}


const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'America/New_York',
};

export const utcToNnewYorkDateFormatter = new Intl.DateTimeFormat('en-CA', options);

export const utcToNnewYorkDatePrinter = (timestamp: string)=> {
    const formatter = new Intl.DateTimeFormat('en-CA', options);
    return formatter.format(new Date(timestamp));
}
